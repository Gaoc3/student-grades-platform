import sqlite3
import uuid

c = sqlite3.connect('data/tenants/doctor_1.db')
course1 = c.execute('SELECT label, category, max_score, order_index FROM grade_components WHERE semester=1').fetchall()
course2_count = c.execute('SELECT count(*) FROM grade_components WHERE semester=2').fetchone()[0]

if course2_count == 0:
    for row in course1:
        key = 'comp_' + uuid.uuid4().hex[:8]
        c.execute('INSERT INTO grade_components (component_key, label, semester, category, max_score, order_index) VALUES (?, ?, 2, ?, ?, ?)', (key, row[0], row[1], row[2], row[3]))
    c.commit()
    print('Duplicated course1 to course2')
else:
    print('Course 2 already has components')
