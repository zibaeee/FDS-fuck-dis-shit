#!/usr/bin/env python3
import cgi
import mysql.connector
import html

print("Content-Type: text/html\n")

form = cgi.FieldStorage()
action = form.getvalue("action", "")
subjid = form.getvalue("subjid", "")
studid = form.getvalue("studid", "")
code = form.getvalue("code", "")
description = form.getvalue("description", "")
units = form.getvalue("units", "")
schedule = form.getvalue("schedule", "")

if isinstance(subjid, list):
    subjid = subjid[0] if subjid else ""
if isinstance(studid, list):
    studid = studid[0] if studid else ""
if isinstance(code, list):
    code = code[0] if code else ""
if isinstance(description, list):
    description = description[0] if description else ""
if isinstance(units, list):
    units = units[0] if units else ""
if isinstance(schedule, list):
    schedule = schedule[0] if schedule else ""

code = html.escape(code)
description = html.escape(description)
schedule = html.escape(schedule)

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="enrollmentsystem"
    )
    cursor = conn.cursor()
    
    if action == "insert" and code and description and units and schedule:
        cursor.execute(
            "INSERT INTO subjects (code, description, units, schedule) VALUES (%s, %s, %s, %s)",
            (code, description, units, schedule)
        )
        conn.commit()
    elif action == "update" and subjid and code and description and units and schedule:
        cursor.execute(
            "UPDATE subjects SET code=%s, description=%s, units=%s, schedule=%s WHERE id=%s",
            (code, description, units, schedule, subjid)
        )
        conn.commit()
    elif action == "delete" and subjid:
        cursor.execute("DELETE FROM enrollment WHERE subject_id=%s", (subjid,))
        cursor.execute("DELETE FROM subjects WHERE id=%s", (subjid,))
        conn.commit()
        subjid = ""
    
    cursor.execute("SELECT IFNULL(MAX(id), 1999) + 1 FROM subjects")
    next_id = cursor.fetchone()[0]
    
    selected_subject = None
    if subjid:
        cursor.execute(
            "SELECT id, code, description, units, schedule FROM subjects WHERE id=%s",
            (subjid,)
        )
        selected_subject = cursor.fetchone()
    
    cursor.execute("""
        SELECT s.id, s.code, s.description, s.units, s.schedule, COUNT(e.student_id) as num_students
        FROM subjects s
        LEFT JOIN enrollment e ON s.id = e.subject_id
        GROUP BY s.id, s.code, s.description, s.units, s.schedule
        ORDER BY s.id
    """)
    subjects = cursor.fetchall()
    
    enrolled_students = []
    if subjid:
        cursor.execute("""
            SELECT st.id, st.name, st.address, st.gender, st.course, st.year_level
            FROM students st
            JOIN enrollment e ON st.id = e.student_id
            WHERE e.subject_id = %s
        """, (subjid,))
        enrolled_students = cursor.fetchall()
    
    display_id = subjid if selected_subject else next_id
    display_code = selected_subject[1] if selected_subject else ""
    display_desc = selected_subject[2] if selected_subject else ""
    display_units = selected_subject[3] if selected_subject else ""
    display_sched = selected_subject[4] if selected_subject else ""
    
    url_params = ""
    if subjid:
        url_params = f"?subjid={subjid}"
    if studid:
        if url_params:
            url_params += f"&studid={studid}"
        else:
            url_params = f"?studid={studid}"
    
    print(f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #f5f5f5; cursor: pointer; }}
            input[type="text"], input[type="number"] {{ width: 200px; padding: 5px; }}
            input[type="submit"] {{ padding: 8px 16px; margin: 5px; cursor: pointer; }}
            .readonly {{ background-color: #f0f0f0; }}
        </style>
        <script>
            function selectSubject(id) {{
                window.location.href = 'subjects.py?subjid=' + id;
            }}
        </script>
    </head>
    <body>
        <a href="students.py{url_params}">Students</a>
        <h2>Subjects Form</h2>
        
        <table width="100%" cellpadding="10">
            <tr>
                <td width="40%" valign="top">
                    <form action="subjects.py{url_params}" method="post">
                        Subject ID:<br>
                        <input type="text" name="subjid" id="subjid" value="{display_id}" {"readonly class='readonly'" if selected_subject else ""}><br><br>
                        
                        Subject Code:<br>
                        <input type="text" name="code" id="code" value="{html.escape(display_code)}"><br><br>
                        
                        Description:<br>
                        <input type="text" name="description" id="description" value="{html.escape(display_desc)}"><br><br>
                        
                        Units:<br>
                        <input type="text" name="units" id="units" value="{display_units}"><br><br>
                        
                        Schedule:<br>
                        <input type="text" name="schedule" id="schedule" value="{html.escape(display_sched)}"><br><br>
                        
                        <input type="hidden" name="action" id="action">
                        
                        <input type="submit" value="Insert" onclick="document.getElementById('action').value='insert'">
                        <input type="submit" value="Update" onclick="document.getElementById('action').value='update'">
                        <input type="submit" value="Delete" onclick="document.getElementById('action').value='delete'">
                    </form>
                </td>
                <td width="60%" valign="top">
                    <h3>Subjects Table</h3>
                    <table>
                        <tr>
                            <th>ID</th>
                            <th>Code</th>
                            <th>Description</th>
                            <th>Units</th>
                            <th>Schedule</th>
                            <th>#Students</th>
                        </tr>
    """)
    
    for subject in subjects:
        sid = subject[0]
        scode = html.escape(subject[1])
        sdesc = html.escape(subject[2])
        sunits = subject[3]
        ssched = html.escape(subject[4])
        scount = subject[5]
        
        print(f"""
                        <tr onclick="selectSubject({sid})">
                            <td>{sid}</td>
                            <td>{scode}</td>
                            <td>{sdesc}</td>
                            <td>{sunits}</td>
                            <td>{ssched}</td>
                            <td>{scount}</td>
                        </tr>
        """)
    
    print("""
                    </table>
                </td>
            </tr>
        </table>
    """)

    if subjid and (subjects or selected_subject):
        print(f"""
        <h3>Students Enrolled in Subject ID {subjid}</h3>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Address</th>
                <th>Gender</th>
                <th>Course</th>
                <th>Year Level</th>
            </tr>
        """)
        
        for student in enrolled_students:
            stud_id = student[0]
            stud_name = html.escape(student[1])
            stud_address = html.escape(student[2])
            stud_gender = html.escape(student[3])
            stud_course = html.escape(student[4])
            stud_year = student[5]
            
            print(f"""
            <tr>
                <td>{stud_id}</td>
                <td>{stud_name}</td>
                <td>{stud_address}</td>
                <td>{stud_gender}</td>
                <td>{stud_course}</td>
                <td>{stud_year}</td>
            </tr>
            """)
        
        print("</table>")
    
    print("""
    </body>
    </html>
    """)
    
except Exception as e:
    print("<h2>Error</h2>")
    print(f"<pre>{html.escape(str(e))}</pre>")
finally:
    if 'conn' in locals():
        conn.close()
