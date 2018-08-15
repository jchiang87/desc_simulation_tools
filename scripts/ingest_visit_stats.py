import os
import glob
import sqlite3

conn = sqlite3.connect('run1.2p_sensor_visit_info.sqlite')
curs = conn.cursor()
table_name = 'sensor_visit_info'
curs.execute("""CREATE TABLE IF NOT EXISTS {}
             (filter text, visit integer, raft text, sensor text,
             sky_level real, phosim_version text)""".format(table_name))
conn.commit()

txt_files = sorted(glob.glob('DC2-R1-2p-*.txt'))
for txt_file in txt_files:
    with open(txt_file, 'r') as fd:
        rows = [line.strip().split() for line in fd]
    curs.executemany('INSERT INTO {} VALUES (?,?,?,?,?,?)'.format(table_name),
                     rows)
    conn.commit()
conn.close()
