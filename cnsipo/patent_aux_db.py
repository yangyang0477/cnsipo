# -*- coding: utf-8 -*-

"""
Fill data into an auxiliary patent database
"""

from __future__ import print_function

import sys
from optparse import OptionParser

import psycopg2

from cnsipo.shared import get_logger
from cnsipo.patent_parser import PatentParser

logger = get_logger()

APP_NO = 'app_no'
APP_YEAR = 'app_year'
COUNTRY = 'country'
STATE = 'state'
ADDRESS = 'address'
APPLICANT = 'applicant'
ATTRS = 'attrs'
patent_parser = None


def gen_patents(conn, table, fld, year, batch_size):
    stmt = "SELECT {}, {} FROM {} WHERE "\
           "extract(year from app_date) = {};".format(APP_NO, fld, table, year)
    sort_fld = globals()["sort_" + fld]
    with conn.cursor() as cursor:
        try:
            logger.debug("executing {}".format(stmt))
            cursor.execute(stmt)
            while True:
                results = cursor.fetchmany(batch_size)
                if results:
                    yield sort_fld(results, year)
                else:
                    break
        except psycopg2.DatabaseError as e:
            logger.error("unexpected database error: {}".format(e))


def sort_address(records, year):
    for record in records:
        result = {APP_YEAR: year}
        result[APP_NO], address = record
        result[COUNTRY], result[STATE] = patent_parser.parse_address(address)
        yield result


def save_sorted_address(conn, table, aux_tbl, year, batch_size, dry_run=False):
    flds = [APP_NO, APP_YEAR, COUNTRY, STATE]
    stmt = "INSERT INTO {} ({}) VALUES ({});".format(
        aux_tbl, ",".join(flds), ",".join(["%(" + i + ")s" for i in flds]))
    if dry_run:
        print("executing {}".format(stmt))
        return

    with conn.cursor() as cursor:
        logger.debug("executing {}".format(stmt))
        try:
            for results in gen_patents(conn, table, ADDRESS, year, batch_size):
                cursor.executemany(stmt, results)
            conn.commit()
        except psycopg2.DatabaseError as e:
            logger.error("unexpected database error: {}".format(e))
            return


def sort_applicant(records, year):
    for record in records:
        result = {}
        result[APP_NO], applicants = record
        parsed = patent_parser.parse_applicants(applicants)
        attrs = 0
        for i, val in enumerate(parsed):
            attrs += ((1 << i) if val else 0)
        result[ATTRS] = attrs
        yield result


def save_sorted_applicant(conn, table, aux_tbl, year, batch_size,
                          dry_run=False):
    stmt = "UPDATE {} SET {}={} WHERE {}={};".format(
        aux_tbl, ATTRS, "%(" + ATTRS + ")s", APP_NO, "%(" + APP_NO + ")s")
    if dry_run:
        print("executing {}".format(stmt))
        return

    with conn.cursor() as cursor:
        logger.debug("executing {}".format(stmt))
        try:
            for results in gen_patents(conn, table, APPLICANT, year,
                                       batch_size):
                cursor.executemany(stmt, results)
            conn.commit()
        except psycopg2.DatabaseError as e:
            logger.error("unexpected database error: {}".format(e))
            return


def main(argv=None):
    usage = "usage: %prog [options] address|applicant year1 [year2 ...]"
    parser = OptionParser(usage)
    import getpass
    username = getpass.getuser()

    parser.add_option("-d", "--database", dest="database", default="cnsipo",
                      help="database name")
    parser.add_option("-u", "--user", dest="user", default=username,
                      help="database username")
    parser.add_option("-p", "--password", dest="password",
                      help="database password")
    parser.add_option("-H", "--host", dest="host", default="localhost",
                      help="database host")
    parser.add_option("-t", "--patent-table", dest="patent_detail_tbl",
                      default="patent_detail",
                      help="patent table")
    parser.add_option("-a", "--patent-aux-table", dest="patent_aux_tbl",
                      default="patent_aux",
                      help="patent auxiliary table")
    parser.add_option("-b", "--batch-size", dest="batch_size", default="1000",
                      help="size of batch insertion")
    parser.add_option("-l", "--loc-file", dest="loc_file",
                      default="LocList.xml",
                      help="country/state/city list")
    parser.add_option("-n", "--dry-run", action="store_true", dest="dry_run",
                      help="show what would have been done")
    (options, args) = parser.parse_args(argv)

    global patent_parser
    patent_parser = PatentParser(options.loc_file)

    if len(args) < 2:
        parser.error("missing arguments")

    fld = args.pop(0)
    if fld not in [ADDRESS, APPLICANT]:
        parser.error("unknown field name: {}".format(fld))

    save_sorted_fld = globals()["save_sorted_" + fld]
    detail_tbl = options.patent_detail_tbl
    aux_tbl = options.patent_aux_tbl
    batch_size = int(options.batch_size)
    dry_run = options.dry_run

    with psycopg2.connect(
            "dbname='{}' user='{}' host='{}' password='{}'".format(
                options.database, options.user,
                options.host, options.password)) as conn:
        for year in args:
            print("processing on patents in year {}".format(year),
                  file=sys.stderr)
            save_sorted_fld(conn, detail_tbl, aux_tbl, year,
                            batch_size=batch_size, dry_run=dry_run)
    return 0


if __name__ == '__main__':
    sys.exit(main())
