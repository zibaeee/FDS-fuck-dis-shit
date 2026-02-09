#!/usr/bin/env python3
import cgi
import mysql.connector
import html

print("Content-Type: text/html\n")

form = cgi.FieldStorage()
action = form.getvalue("action", "")
tid = form.getvalue("tid", "")
subjid = form.getvalue("subjid", "")
name = form.getvalue("name", "")
department = form.getvalue("department", "")
address = form.getvalue("address", "")
contact = form.getvalue("contact", "")
status = form.getvalue("status", "")

if isinstance(tid, list):
    tid = tid[0] if tid else ""
if isinstance(subjid, list):
    subjid = subjid[0] if subjid else ""
if isinstance(name, list):
    name = name[0] if name else ""
if isinstance(department, list):
    department = department[0] if department else ""
if isinstance(address, list):
    address = address[0] if address else ""
if isinstance(contact, list):
    contact = contact[0] if contact else ""
if isinstance(status, list):
    status = status[0] if status else ""

name = html.escape(name)
department = html.escape(department)
address = html.escape(address)
contact = html.escape(contact)
status = html.escape(status)

def check_schedule_conflict(schedule1, schedule2):
    """Check if two schedules conflict"""
    conflicting_sets = [
        ["MWF 11:00-12:00", "MWF 09:00-11:00", "TTH 10:40-11:25"]
    ]
    
    for conflict_set in conflicting_sets:
        if schedule1 in conflict_set and schedule2 in conflict_set:
            return True
    
    return False

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="enrollmentsystem"
    )
    cursor = conn.cursor()
    
    if action == "insert" and name and department and address and contact and status:
        cursor.execute(
            "INSERT INTO teachers (name, department, address, contact, status) VALUES (%s, %s, %s, %s, %s)",
            (name, department, address, contact, status)
        )
        conn.commit()
    elif action == "update" and tid and name and department and address and contact and status:
        cursor.execute(
            "UPDATE teachers SET name=%s, department=%s, address=%s, contact=%s, status=%s WHERE id=%s",
            (name, department, address, contact, status, tid)
        )
        conn.commit()
    elif action == "delete" and tid:
        cursor.execute("DELETE FROM teacher_assignments WHERE teacher_id=%s", (tid,))
        cursor.execute("DELETE FROM teachers WHERE id=%s", (tid,))
        conn.commit()
        tid = ""
    elif action == "assign" and tid and subjid:
        cursor.execute(
            "INSERT INTO teacher_assignments (teacher_id, subject_id) VALUES (%s, %s)",
            (tid, subjid)
        )
        conn.commit()
    elif action == "unassign" and tid and subjid:
        unassign_subjid = form.getvalue("unassign_subjid", "")
        if unassign_subjid:
            cursor.execute(
                "DELETE FROM teacher_assignments WHERE teacher_id=%s AND subject_id=%s",
                (tid, unassign_subjid)
            )
            conn.commit()
    
    cursor.execute("SELECT IFNULL(MAX(id), 2999) + 1 FROM teachers")
    next_id = cursor.fetchone()[0]
    
    selected_teacher = None
    if tid:
        cursor.execute(
            "SELECT id, name, department, address, contact, status FROM teachers WHERE id=%s",
            (tid,)
        )
        selected_teacher = cursor.fetchone()
    
    cursor.execute("""
        SELECT t.id, t.name, t.department, t.contact, t.status, 
               COUNT(ta.subject_id) as num_subjects,
               IFNULL(SUM(s.units), 0) as total_units
        FROM teachers t
        LEFT JOIN teacher_assignments ta ON t.id = ta.teacher_id
        LEFT JOIN subjects s ON ta.subject_id = s.id
        GROUP BY t.id, t.name, t.department, t.contact, t.status
        ORDER BY t.id
    """)
    teachers = cursor.fetchall()
    
    assigned_subjects = []
    if tid:
        cursor.execute("""
            SELECT s.id, s.code, s.description, s.units, s.schedule 
            FROM subjects s
            JOIN teacher_assignments ta ON s.id = ta.subject_id
            WHERE ta.teacher_id = %s
        """, (tid,))
        assigned_subjects = cursor.fetchall()
    
    is_assigned = False
    if tid and subjid:
        cursor.execute(
            "SELECT 1 FROM teacher_assignments WHERE teacher_id=%s AND subject_id=%s",
            (tid, subjid)
        )
        is_assigned = cursor.fetchone() is not None
    
    subject_assigned_to_other = False
    if subjid:
        cursor.execute(
            "SELECT teacher_id FROM teacher_assignments WHERE subject_id=%s",
            (subjid,)
        )
        result = cursor.fetchone()
        if result and result[0] != int(tid) if tid else None:
            subject_assigned_to_other = True
    
    selected_subject = None
    selected_subject_schedule = None
    if subjid:
        cursor.execute("SELECT id, code, schedule FROM subjects WHERE id=%s", (subjid,))
        result = cursor.fetchone()
        if result:
            selected_subject = result
            selected_subject_schedule = result[2]
    
    conflict_subject = None
    if tid and subjid and selected_subject_schedule:
        for assigned in assigned_subjects:
            assigned_schedule = assigned[4]
            if check_schedule_conflict(selected_subject_schedule, assigned_schedule):
                conflict_subject = assigned
                break
    
    display_id = tid if selected_teacher else next_id
    display_name = selected_teacher[1] if selected_teacher else ""
    display_dept = selected_teacher[2] if selected_teacher else ""
    display_address = selected_teacher[3] if selected_teacher else ""
    display_contact = selected_teacher[4] if selected_teacher else ""
    display_status = selected_teacher[5] if selected_teacher else ""
    
    url_params = ""
    if tid:
        url_params = f"?tid={tid}"
    if subjid:
        if url_params:
            url_params += f"&subjid={subjid}"
        else:
            url_params = f"?subjid={subjid}"
    
    print(f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            .header {{ background-color: #003366; color: white; padding: 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 36px; letter-spacing: 2px; }}
            .header h2 {{ margin: 5px 0 0 0; font-size: 18px; font-weight: normal; }}
            .nav {{ background-color: #f0f0f0; padding: 10px; text-align: center; }}
            .nav a {{ margin: 0 15px; text-decoration: none; color: #003366; font-weight: bold; }}
            .nav a:hover {{ text-decoration: underline; }}
            .nav span {{ margin: 0 15px; color: #999; font-weight: bold; }}
            .content {{ margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #f5f5f5; cursor: pointer; }}
            input[type="text"] {{ width: 200px; padding: 5px; }}
            input[type="submit"] {{ padding: 8px 16px; margin: 5px; cursor: pointer; }}
            .readonly {{ background-color: #f0f0f0; }}
            .conflict {{ color: red; font-weight: bold; margin: 10px 0; }}
            .message {{ color: blue; font-weight: bold; margin: 10px 0; }}
        </style>
        <script>
            function selectTeacher(id) {{
                var url = 'teachers.py?tid=' + id;
                var subjid = '{subjid}';
                if (subjid) {{
                    url += '&subjid=' + subjid;
                }}
                window.location.href = url;
            }}
            
            function selectAssignedSubject(subjid) {{
                var tid = document.getElementById("tid").value;
                if (tid) {{
                    window.location.href = 'teachers.py?tid=' + tid + '&subjid=' + subjid + '&unassign_subjid=' + subjid;
                }}
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h1>STUDENT INFORMATION SYSTEM</h1>
            <h2>Ateneo de Davao University</h2>
        </div>
        
        <div class="nav">
            <a href="students.py{url_params}">Students</a>
            <a href="subjects.py{url_params}">Subjects</a>
            <span>Teachers</span>
        </div>
        
        <div class="content">
        <h2>Teachers Form</h2>
        
        <table width="100%" cellpadding="10">
            <tr>
                <td width="40%" valign="top">
                    <form action="teachers.py{url_params}" method="post">
                        Teacher ID:<br>
                        <input type="text" name="tid" id="tid" value="{display_id}" {"readonly class='readonly'" if selected_teacher else ""}><br><br>
                        
                        Name:<br>
                        <input type="text" name="name" id="name" value="{html.escape(display_name)}"><br><br>
                        
                        Department:<br>
                        <input type="text" name="department" id="department" value="{html.escape(display_dept)}"><br><br>
                        
                        Address:<br>
                        <input type="text" name="address" id="address" value="{html.escape(display_address)}"><br><br>
                        
                        Contact:<br>
                        <input type="text" name="contact" id="contact" value="{html.escape(display_contact)}"><br><br>
                        
                        Status:<br>
                        <input type="text" name="status" id="status" value="{html.escape(display_status)}"><br><br>
                        
                        <input type="hidden" name="action" id="action">
                        
                        <input type="submit" value="Insert" onclick="document.getElementById('action').value='insert'">
                        <input type="submit" value="Update" onclick="document.getElementById('action').value='update'">
                        <input type="submit" value="Delete" onclick="document.getElementById('action').value='delete'"><br><br>
    """)
    
    if subjid and selected_subject and tid:
        if subject_assigned_to_other:
            print('<div class="message">This subject is already assigned to another teacher</div>')
        elif is_assigned:
            print('<div class="message">This teacher is already assigned to this subject</div>')
        elif conflict_subject:
            print(f'<div class="conflict">Conflict with {html.escape(conflict_subject[1])} - {html.escape(conflict_subject[4])}</div>')
        else:
            assign_text = f"Assign Teacher ID: {tid} to Subject ID: {subjid}"
            print(f"""
                        <input type="submit" value="{assign_text}" onclick="document.getElementById('action').value='assign'">
            """)
    elif subjid and selected_subject and not tid:
        assign_text = f"Assign Teacher ID: (?) to Subject ID: {subjid}"
        print(f'<div class="message">{assign_text}</div>')
    
    if form.getvalue("unassign_subjid", ""):
        unassign_subjid_val = form.getvalue("unassign_subjid", "")
        unassign_text = f"Unassign Subject ID: {unassign_subjid_val} from Teacher ID: {tid}"
        print(f"""
                        <input type="submit" value="{unassign_text}" onclick="document.getElementById('action').value='unassign'">
                        <input type="hidden" name="unassign_subjid" value="{unassign_subjid_val}">
        """)
    
    print("""
                    </form>
                </td>
                <td width="60%" valign="top">
                    <h3>Teachers Table</h3>
                    <table>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Department</th>
                            <th>Contact</th>
                            <th>Status</th>
                            <th>#Subjects</th>
                            <th>TotUnits</th>
                        </tr>
    """)
    
    for teacher in teachers:
        teacher_id = teacher[0]
        teacher_name = html.escape(teacher[1])
        teacher_dept = html.escape(teacher[2])
        teacher_contact = html.escape(teacher[3])
        teacher_status = html.escape(teacher[4])
        teacher_subjs = teacher[5]
        teacher_units = teacher[6]
        
        print(f"""
                        <tr onclick="selectTeacher({teacher_id})">
                            <td>{teacher_id}</td>
                            <td>{teacher_name}</td>
                            <td>{teacher_dept}</td>
                            <td>{teacher_contact}</td>
                            <td>{teacher_status}</td>
                            <td>{teacher_subjs}</td>
                            <td>{teacher_units}</td>
                        </tr>
        """)
    
    print("""
                    </table>
                </td>
            </tr>
        </table>
    """)
    
    if tid and selected_teacher:
        print(f"""
        <h3>Assigned Subjects</h3>
        <table>
            <tr>
                <th>Subject ID</th>
                <th>Code</th>
                <th>Description</th>
                <th>Units</th>
                <th>Schedule</th>
            </tr>
        """)
        
        for subject in assigned_subjects:
            subj_id = subject[0]
            subj_code = html.escape(subject[1])
            subj_desc = html.escape(subject[2])
            subj_units = subject[3]
            subj_sched = html.escape(subject[4])
            
            print(f"""
            <tr onclick="selectAssignedSubject({subj_id})">
                <td>{subj_id}</td>
                <td>{subj_code}</td>
                <td>{subj_desc}</td>
                <td>{subj_units}</td>
                <td>{subj_sched}</td>
            </tr>
            """)
        
        print("</table>")
    
    print("""
        </div>
    </body>
    </html>
    """)
    
except Exception as e:
    print("<h2>Error</h2>")
    print(f"<pre>{html.escape(str(e))}</pre>")
finally:
    if 'conn' in locals():
        conn.close()
