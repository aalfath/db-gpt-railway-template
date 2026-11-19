"""Create and upgrade DB-GPT's metadata schema in the MySQL service.

Runs before the webserver on every start (railway-start.sh):
1. waits for MySQL (up to DB_WAIT_SECONDS, default 300),
2. creates the metadata database if it is missing,
3. fresh database: loads the image's own assets/schema/dbgpt.sql (without its demo EXAMPLE_1 database),
   existing database: applies each upstream assets/schema/upgrade/vX_Y_Z/upgrade_to_*.sql newer than
   the recorded version, in order, skipping changes that are already there,
4. records the schema version in the railway_template_meta table.
DB-GPT itself does not run DDL on MySQL ("for safety considerations"), so this is upstream's manual
step, automated.
"""
import glob
import os
import re
import sys
import time

import pymysql
import sqlparse

from dbgpt_app._version import version as APP_VERSION

SCHEMA = "/app/assets/schema/dbgpt.sql"
UPGRADES = "/app/assets/schema/upgrade"
# Already-applied changes: duplicate column, duplicate key name, table exists, can't drop missing
# field/key, duplicate entry for unique index rebuilds.
IGNORABLE = {1050, 1060, 1061, 1091, 1062, 1826}


def log(msg):
    print(f"[railway-db-init] {msg}", flush=True)


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def connect(db=None):
    return pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ.get("MYSQL_PORT") or 3306),
        user=os.environ.get("MYSQL_USER") or "root",
        password=os.environ["MYSQL_PASSWORD"],
        database=db,
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=10,
    )


def statements(sql, dbname):
    # Upstream files hard-code the database name `dbgpt`.
    sql = re.sub(r"(?im)^\s*use\s+dbgpt\s*;", f"USE `{dbname}`;", sql)
    sql = re.sub(r"(?is)CREATE\s+DATABASE\s+IF\s+NOT\s+EXISTS\s+dbgpt\s*;", "", sql)
    for st in sqlparse.split(sql):
        st = st.strip()
        body = sqlparse.format(st, strip_comments=True).strip()
        if body and body != ";":
            yield st


def run_file(cur, path, dbname, tolerant):
    sql = open(path, encoding="utf-8").read()
    if path == SCHEMA:
        # Drop upstream's demo database (EXAMPLE_1 with sample users) at the end of the file.
        cut = sql.find("-- Example database for chat users")
        if cut != -1:
            sql = sql[:cut]
    n = 0
    for st in statements(sql, dbname):
        try:
            cur.execute(st)
            n += 1
        except pymysql.err.MySQLError as e:
            code = e.args[0] if e.args else None
            if tolerant and code in IGNORABLE:
                continue
            log(f"failed in {os.path.basename(path)}: {e}")
            raise
    log(f"applied {os.path.basename(path)} ({n} statements)")


def main():
    dbname = os.environ.get("DBGPT_MYSQL_DATABASE") or "dbgpt"
    if not re.fullmatch(r"[A-Za-z0-9_]+", dbname):
        sys.exit("DBGPT_MYSQL_DATABASE may only contain letters, digits and _")
    deadline = time.time() + int(os.environ.get("DB_WAIT_SECONDS") or 300)
    while True:
        try:
            conn = connect()
            break
        except pymysql.err.MySQLError as e:
            if time.time() > deadline:
                log(f"MySQL not reachable: {e}")
                sys.exit(1)
            log(f"waiting for MySQL at {os.environ.get('MYSQL_HOST')}: {e}")
            time.sleep(3)
    cur = conn.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{dbname}` "
        "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cur.execute(f"USE `{dbname}`")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS railway_template_meta "
        "(k VARCHAR(64) PRIMARY KEY, v VARCHAR(255) NOT NULL)"
    )
    cur.execute("SELECT v FROM railway_template_meta WHERE k='schema_version'")
    row = cur.fetchone()
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema=%s AND table_name='knowledge_space'",
        (dbname,),
    )
    has_tables = cur.fetchone()[0] > 0
    current = vtuple(APP_VERSION)
    if row is None and not has_tables:
        log(f"new database `{dbname}`: loading DB-GPT {APP_VERSION} schema")
        run_file(cur, SCHEMA, dbname, tolerant=True)
    else:
        recorded = vtuple(row[0]) if row else current
        if row is None:
            log("tables exist but no recorded version; assuming the image's version")
        todo = []
        for d in glob.glob(os.path.join(UPGRADES, "v*")):
            v = vtuple(os.path.basename(d))
            if recorded < v <= current:
                todo += [(v, f) for f in glob.glob(os.path.join(d, "upgrade_to*.sql"))]
        for v, f in sorted(todo):
            log(f"upgrading schema to {'.'.join(map(str, v))}")
            run_file(cur, f, dbname, tolerant=True)
        if not todo:
            log(f"schema is up to date ({APP_VERSION})")
    cur.execute(
        "REPLACE INTO railway_template_meta (k, v) VALUES ('schema_version', %s)",
        (APP_VERSION,),
    )
    conn.close()


if __name__ == "__main__":
    main()
