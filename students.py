#!/usr/bin/env python3
import cgi
import mysql.connector
import html

print("Content-Type: text/html\n")

form = cgi.FieldStorage()
action = form.getvalue("action", "")
studid = form.getvalue("studid", "")
subjid = form.getvalue("subjid", "")
name = form.getvalue("name", "")
address = form.getvalue("address", "")
gender = form.getvalue("gender", "")
course = form.getvalue("course", "")
year_level = form.getvalue("year_level", "")

if isinstance(studid, list):
    studid = studid[0] if studid else ""
if isinstance(subjid, list):
    subjid = subjid[0] if subjid else ""
if isinstance(name, list):
    name = name[0] if name else ""
if isinstance(address, list):
    address = address[0] if address else ""
if isinstance(gender, list):
    gender = gender[0] if gender else ""
if isinstance(course, list):
    course = course[0] if course else ""
if isinstance(year_level, list):
    year_level = year_level[0] if year_level else ""

name = html.escape(name)
address = html.escape(address)
gender = html.escape(gender)
course = html.escape(course)

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="enrollmentsystem"
    )
    cursor = conn.cursor()
    
    if action == "insert" and name and address and gender and course and year_level:
        cursor.execute(
            "INSERT INTO students (name, address, gender, course, year_level) VALUES (%s, %s, %s, %s, %s)",
            (name, address, gender, course, year_level)
        )
        conn.commit()
    elif action == "update" and studid and name and address and gender and course and year_level:
        cursor.execute(
            "UPDATE students SET name=%s, address=%s, gender=%s, course=%s, year_level=%s WHERE id=%s",
            (name, address, gender, course, year_level, studid)
        )
        conn.commit()
    elif action == "delete" and studid:
        cursor.execute("DELETE FROM enrollment WHERE student_id=%s", (studid,))
        cursor.execute("DELETE FROM students WHERE id=%s", (studid,))
        conn.commit()
        studid = ""
    elif action == "enroll" and studid and subjid:
        cursor.execute(
            "INSERT INTO enrollment (student_id, subject_id) VALUES (%s, %s)",
            (studid, subjid)
        )
        conn.commit()
    elif action == "drop" and studid and subjid:
        drop_subjid = form.getvalue("drop_subjid", "")
        if drop_subjid:
            cursor.execute(
                "DELETE FROM enrollment WHERE student_id=%s AND subject_id=%s",
                (studid, drop_subjid)
            )
            conn.commit()
    
    cursor.execute("SELECT IFNULL(MAX(id), 999) + 1 FROM students")
    next_id = cursor.fetchone()[0]
    
    selected_student = None
    if studid:
        cursor.execute(
            "SELECT id, name, address, gender, course, year_level FROM students WHERE id=%s",
            (studid,)
        )
        selected_student = cursor.fetchone()
    
    cursor.execute("""
        SELECT s.id, s.name, s.address, s.gender, s.course, s.year_level, 
               IFNULL(SUM(subj.units), 0) as total_units
        FROM students s
        LEFT JOIN enrollment e ON s.id = e.student_id
        LEFT JOIN subjects subj ON e.subject_id = subj.id
        GROUP BY s.id, s.name, s.address, s.gender, s.course, s.year_level
        ORDER BY s.id
    """)
    students = cursor.fetchall()
    
    enrolled_subjects = []
    if studid:
        cursor.execute("""
            SELECT s.id, s.code, s.description, s.units, s.schedule 
            FROM subjects s
            JOIN enrollment e ON s.id = e.subject_id
            WHERE e.student_id = %s
        """, (studid,))
        enrolled_subjects = cursor.fetchall()
    
    is_enrolled = False
    if studid and subjid:
        cursor.execute(
            "SELECT 1 FROM enrollment WHERE student_id=%s AND subject_id=%s",
            (studid, subjid)
        )
        is_enrolled = cursor.fetchone() is not None
    
    selected_subject = None
    if subjid:
        cursor.execute("SELECT id, code FROM subjects WHERE id=%s", (subjid,))
        selected_subject = cursor.fetchone()
    
    display_id = studid if selected_student else next_id
    display_name = selected_student[1] if selected_student else ""
    display_address = selected_student[2] if selected_student else ""
    display_gender = selected_student[3] if selected_student else ""
    display_course = selected_student[4] if selected_student else ""
    display_year = selected_student[5] if selected_student else ""
    
    url_params = ""
    if studid:
        url_params = f"?studid={studid}"
    if subjid:
        if url_params:
            url_params += f"&subjid={subjid}"
        else:
            url_params = f"?subjid={subjid}"
    
    print(f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #f5f5f5; cursor: pointer; }}
            input[type="text"], input[type="number"], select {{ width: 200px; padding: 5px; }}
            input[type="submit"] {{ padding: 8px 16px; margin: 5px; cursor: pointer; }}
            .readonly {{ background-color: #f0f0f0; }}
        </style>
        <script>
            function selectStudent(id) {{
                var url = 'students.py?studid=' + id;
                var subjid = '{subjid}';
                if (subjid) {{
                    url += '&subjid=' + subjid;
                }}
                window.location.href = url;
            }}
            
            function selectEnrolledSubject(subjid) {{
                var studid = document.getElementById("studid").value;
                if (studid) {{
                    window.location.href = 'students.py?studid=' + studid + '&subjid=' + subjid + '&drop_subjid=' + subjid;
                }}
            }}
        </script>
    </head>
    <body>
        <a href="subjects.py{url_params}">Subjects</a>
        <h2>Student Form</h2>
        
        <table width="100%" cellpadding="10">
            <tr>
                <td width="40%" valign="top">
                    <form action="students.py{url_params}" method="post">
                        Student ID:<br>
                        <input type="text" name="studid" id="studid" value="{display_id}" {"readonly class='readonly'" if selected_student else ""}><br><br>
                        
                        Name:<br>
                        <input type="text" name="name" id="name" value="{html.escape(display_name)}"><br><br>
                        
                        Address:<br>
                        <input type="text" name="address" id="address" value="{html.escape(display_address)}"><br><br>
                        
                        Gender:<br>
                        <input type="text" name="gender" id="gender" value="{html.escape(display_gender)}"><br><br>
                        
                        Course:<br>
                        <input type="text" name="course" id="course" value="{html.escape(display_course)}"><br><br>
                        
                        Year Level:<br>
                        <input type="text" name="year_level" id="year_level" value="{display_year}"><br><br>
                        
                        <input type="hidden" name="action" id="action">
                        {"" if subjid else '<input type="hidden" name="subjid" value="">'}
                        
                        <input type="submit" value="Insert" onclick="document.getElementById('action').value='insert'">
                        <input type="submit" value="Update" onclick="document.getElementById('action').value='update'">
                        <input type="submit" value="Delete" onclick="document.getElementById('action').value='delete'"><br><br>
    """)
    
    if subjid and selected_subject and not is_enrolled:
        enroll_text = f"Enroll Student ID: ({studid if studid else '?'}) to Subject ID: {subjid}"
        print(f"""
                        <input type="submit" value="{enroll_text}" onclick="document.getElementById('action').value='enroll'">
        """)
    
    if form.getvalue("drop_subjid", ""):
        drop_subjid_val = form.getvalue("drop_subjid", "")
        drop_text = f"Drop Subject ID: {drop_subjid_val} of Student ID: {studid}"
        print(f"""
                        <input type="submit" value="{drop_text}" onclick="document.getElementById('action').value='drop'">
                        <input type="hidden" name="drop_subjid" value="{drop_subjid_val}">
        """)
    
    print("""
                    </form>
                </td>
                <td width="60%" valign="top">
                    <h3>Students Table</h3>
                    <table>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Address</th>
                            <th>Gender</th>
                            <th>Course</th>
                            <th>Year</th>
                            <th>Total Units</th>
                        </tr>
    """)
    
    for student in students:
        sid = student[0]
        sname = html.escape(student[1])
        saddress = html.escape(student[2])
        sgender = html.escape(student[3])
        scourse = html.escape(student[4])
        syear = student[5]
        sunits = student[6]
        
        print(f"""
                        <tr onclick="selectStudent({sid})">
                            <td>{sid}</td>
                            <td>{sname}</td>
                            <td>{saddress}</td>
                            <td>{sgender}</td>
                            <td>{scourse}</td>
                            <td>{syear}</td>
                            <td>{sunits}</td>
                        </tr>
        """)
    
    print("""
                    </table>
                </td>
            </tr>
        </table>
        
        <h3>Enrolled Subjects</h3>
        <table>
            <tr>
                <th>Subject ID</th>
                <th>Code</th>
                <th>Description</th>
                <th>Units</th>
                <th>Schedule</th>
            </tr>
    """)
    
    for subject in enrolled_subjects:
        subj_id = subject[0]
        subj_code = html.escape(subject[1])
        subj_desc = html.escape(subject[2])
        subj_units = subject[3]
        subj_sched = html.escape(subject[4])
        
        print(f"""
            <tr onclick="selectEnrolledSubject({subj_id})">
                <td>{subj_id}</td>
                <td>{subj_code}</td>
                <td>{subj_desc}</td>
                <td>{subj_units}</td>
                <td>{subj_sched}</td>
            </tr>
        """)
    
    print("""
        </table>
    </body>
    </html>
    """)
    
except Exception as e:
    print("<h2>Error</h2>")
    print(f"<pre>{html.escape(str(e))}</pre>")
finally:
    if 'conn' in locals():
        conn.close()
