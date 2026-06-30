import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time,datetime
import pymysql
import sqlite3
import os
import socket
import platform
import geocoder
import secrets
import io,random
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import sys
sys.path.insert(0, '..')
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import getpass
import os
import nltk

nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

from pyresparser import ResumeParser

def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course
connection = sqlite3.connect('cv.db', check_same_thread=False)
cursor = connection.cursor()
def insert_data(sec_token,ip_add,host_name,dev_user,os_name_ver,latlong,city,state,country,act_name,act_mail,act_mob,name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses,pdf_name):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    rec_values = (str(sec_token),str(ip_add),host_name,dev_user,os_name_ver,str(latlong),city,state,country,act_name,act_mail,act_mob,name,email,str(res_score),timestamp,str(no_of_pages),reco_field,cand_level,skills,recommended_skills,courses,pdf_name)
    cursor.execute(insert_sql, rec_values)
    connection.commit()
def insertf_data(feed_name,feed_email,feed_score,comments,Timestamp):
    DBf_table_name = 'user_feedback'
    insertfeed_sql = "insert into " + DBf_table_name + """
    values (NULL,?,?,?,?,?)"""
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    connection.commit()
st.set_page_config(
   page_title="AI Resume Analyzer",
   page_icon='./Logo/recommend.png',
   layout="wide",
   initial_sidebar_state="collapsed",
)
with open(os.path.join(os.path.dirname(__file__), 'style.css')) as f:
    css = f.read()
st.markdown(f'<style>\n{css}\n</style>', unsafe_allow_html=True)
def run():
    img = Image.open(os.path.join(os.path.dirname(__file__), 'Logo', 'RESUM.png'))
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.image(img, width=100)
    with col_title:
        st.markdown("""
        <div style="padding-top: 0.5rem;">
            <h1 style="font-size:2.2rem; font-weight:800; margin:0;
                background: linear-gradient(135deg, #6C63FF, #00D2FF, #FF6584);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text;">
                AI Resume Analyzer
            </h1>
            <p style="color:#A0AEC0; font-size:0.95rem; margin-top:0.2rem;">
                Smart resume parsing, skill recommendations & career insights powered by NLP
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('<hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:1rem 0 0.8rem;">', unsafe_allow_html=True)
    page_slugs = ['user', 'bulk', 'feedback', 'about', 'admin']
    try:
        url_page = st.query_params.get("page", "user").lower()
    except:
        try:
            qp = st.experimental_get_query_params()
            url_page = qp.get("page", ["user"])[0].lower()
        except:
            url_page = "user"
    if url_page not in page_slugs:
        url_page = 'user'
    if 'current_page' not in st.session_state:
        st.session_state.current_page = url_page
    nav_items = [
        ('user',     '👤', 'User'),
        ('bulk',     '📁', 'Bulk Upload'),
        ('feedback', '💬', 'Feedback'),
        ('about',    'ℹ️',  'About'),
        ('admin',    '🔐', 'Admin'),
    ]
    # Look for this block in App.py (approx lines 105-115)
    cols = st.columns(len(nav_items))
    for col, (slug, icon, label) in zip(cols, nav_items):
        is_active = (st.session_state.current_page == slug)
        btn_type = 'primary' if is_active else 'secondary'
        with col:
            if st.button(f'{icon}  {label}', key=f'nav_{slug}', type=btn_type, use_container_width=True):
                st.session_state.current_page = slug
                try:
                    st.query_params["page"] = slug
                except:
                    try:
                        st.experimental_set_query_params(page=slug)
                    except:
                        pass
                st.rerun()
    slug_to_choice = {
        'user':     '👤  User',
        'bulk':     '📁  Bulk Upload',
        'feedback': '💬  Feedback',
        'about':    'ℹ️  About',
        'admin':    '🔐  Admin',
    }
    choice = slug_to_choice.get(st.session_state.current_page, '👤  User')
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    sec_token varchar(20) NOT NULL,
                    ip_add varchar(50) NULL,
                    host_name varchar(50) NULL,
                    dev_user varchar(50) NULL,
                    os_name_ver varchar(50) NULL,
                    latlong varchar(50) NULL,
                    city varchar(50) NULL,
                    state varchar(50) NULL,
                    country varchar(50) NULL,
                    act_name varchar(50) NOT NULL,
                    act_mail varchar(50) NOT NULL,
                    act_mob varchar(20) NOT NULL,
                    Name varchar(500) NOT NULL,
                    Email_ID VARCHAR(500) NOT NULL,
                    resume_score VARCHAR(8) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL,
                    Page_no VARCHAR(5) NOT NULL,
                    Predicted_Field BLOB NOT NULL,
                    User_level BLOB NOT NULL,
                    Actual_skills BLOB NOT NULL,
                    Recommended_skills BLOB NOT NULL,
                    Recommended_courses BLOB NOT NULL,
                    pdf_name varchar(50) NOT NULL
                    );
                """
    cursor.execute(table_sql)
    DBf_table_name = 'user_feedback'
    tablef_sql = "CREATE TABLE IF NOT EXISTS " + DBf_table_name + """
                    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        feed_name varchar(50) NOT NULL,
                        feed_email VARCHAR(50) NOT NULL,
                        feed_score VARCHAR(5) NOT NULL,
                        comments VARCHAR(100) NULL,
                        Timestamp VARCHAR(50) NOT NULL
                    );
                """
    cursor.execute(tablef_sql)
    if choice == '👤  User':
        st.markdown("""
        <div class="glass-card">
            <div class="section-header">
                <div class="icon">👤</div>
                <div>
                    <div class="text">Your Information</div>
                    <div class="subtext">Please fill in your details to get started</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            act_name = st.text_input('Name*', placeholder='John Doe')
        with col2:
            act_mail = st.text_input('Mail*', placeholder='john@example.com')
        with col3:
            act_mob  = st.text_input('Mobile Number*', placeholder='+91 9876543210')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        try:
            dev_user = os.getlogin()
        except OSError:
            dev_user = getpass.getuser()
        os_name_ver = platform.system() + " " + platform.release()
        g = geocoder.ip('me')
        latlong = g.latlng
        geolocator = Nominatim(user_agent="http")
        location = geolocator.reverse(latlong, language='en')
        address = location.raw['address']
        cityy = address.get('city', '')
        statee = address.get('state', '')
        countryy = address.get('country', '')  
        city = cityy
        state = statee
        country = countryy
        st.markdown("""
        <div class="glass-card" style="margin-top:1rem;">
            <div class="section-header">
                <div class="icon">📄</div>
                <div>
                    <div class="text">Upload Your Resume</div>
                    <div class="subtext">Upload a PDF resume and get smart AI-powered recommendations</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            os.makedirs(os.path.dirname(save_image_path), exist_ok=True)

            with open(save_image_path, "wb") as f:
                f.write(pdf_name.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                resume_text = pdf_reader(save_image_path)
                st.markdown("""
                <div class="glass-card" style="margin-top:1rem;">
                    <div class="section-header">
                        <div class="icon">📊</div>
                        <div>
                            <div class="text">Resume Analysis</div>
                            <div class="subtext">Here's what our AI extracted from your resume</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.success(f"👋 Hello **{resume_data['name']}**! Here's your personalized analysis.")
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">👤</div>
                        <div>
                            <div class="text">Your Basic Info</div>
                            <div class="subtext">Extracted from your resume</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                try:
                    info_col1, info_col2, info_col3 = st.columns(3)
                    with info_col1:
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="label">Full Name</div>
                            <div class="value">{resume_data['name']}</div>
                        </div>
                        <div class="info-card">
                            <div class="label">Email Address</div>
                            <div class="value">{resume_data['email']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with info_col2:
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="label">Phone Number</div>
                            <div class="value">{resume_data['mobile_number']}</div>
                        </div>
                        <div class="info-card">
                            <div class="label">Degree</div>
                            <div class="value">{str(resume_data['degree'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with info_col3:
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="label">Resume Pages</div>
                            <div class="value">{str(resume_data['no_of_pages'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] < 1:                
                    cand_level = "NA"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-fresher">🌱 Fresher Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">You're just starting out — keep building your skills and projects!</p></div>''',unsafe_allow_html=True)
                elif 'INTERNSHIP' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-intermediate">🚀 Intermediate Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Great! You have internship experience — you're building real-world skills.</p></div>''',unsafe_allow_html=True)
                elif 'INTERNSHIPS' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-intermediate">🚀 Intermediate Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Great! You have internship experience — you're building real-world skills.</p></div>''',unsafe_allow_html=True)
                elif 'Internship' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-intermediate">🚀 Intermediate Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Great! You have internship experience — you're building real-world skills.</p></div>''',unsafe_allow_html=True)
                elif 'Internships' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-intermediate">🚀 Intermediate Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Great! You have internship experience — you're building real-world skills.</p></div>''',unsafe_allow_html=True)
                elif 'EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-experienced">⭐ Experienced Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Excellent! You have professional work experience — you're a seasoned candidate.</p></div>''',unsafe_allow_html=True)
                elif 'WORK EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-experienced">⭐ Experienced Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Excellent! You have professional work experience — you're a seasoned candidate.</p></div>''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-experienced">⭐ Experienced Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Excellent! You have professional work experience — you're a seasoned candidate.</p></div>''',unsafe_allow_html=True)
                elif 'Work Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-experienced">⭐ Experienced Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">Excellent! You have professional work experience — you're a seasoned candidate.</p></div>''',unsafe_allow_html=True)
                else:
                    cand_level = "Fresher"
                    st.markdown('''<div class="glass-card"><span class="level-badge level-fresher">🌱 Fresher Level</span><p style="color:#A0AEC0; font-size:0.85rem; margin-top:0.5rem;">You're at the fresher level — focus on building projects and gaining experience!</p></div>''',unsafe_allow_html=True)
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">💡</div>
                        <div>
                            <div class="text">Skills Recommendation</div>
                            <div class="subtext">Based on your current skills, here's what we recommend</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',value=resume_data['skills'],key = '1  ')
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''
                for i in resume_data['skills']:
                    if i.lower() in ds_keyword:
                        reco_field = 'Data Science'
                        st.markdown("""
                        <div class="glass-card" style="border-left: 3px solid #6C63FF;">
                            <div style="font-size:1.1rem; font-weight:600; color:#A29BFE; margin-bottom:0.3rem;">🔬 Data Science Detected</div>
                            <div style="color:#A0AEC0; font-size:0.85rem;">Our analysis says you are looking for <b style="color:#fff;">Data Science</b> jobs.</div>
                        </div>
                        """, unsafe_allow_html=True)
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">🚀</span> Adding these skills will boost your chances of getting a Data Science job!</div>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break
                    elif i.lower() in web_keyword:
                        reco_field = 'Web Development'
                        st.markdown("""
                        <div class="glass-card" style="border-left: 3px solid #00D2FF;">
                            <div style="font-size:1.1rem; font-weight:600; color:#74B9FF; margin-bottom:0.3rem;">🌐 Web Development Detected</div>
                            <div style="color:#A0AEC0; font-size:0.85rem;">Our analysis says you are looking for <b style="color:#fff;">Web Development</b> jobs.</div>
                        </div>
                        """, unsafe_allow_html=True)
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">🚀</span> Adding these skills will boost your chances of getting a Web Dev job!</div>''',unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break
                    elif i.lower() in android_keyword:
                        reco_field = 'Android Development'
                        st.markdown("""
                        <div class="glass-card" style="border-left: 3px solid #48BB78;">
                            <div style="font-size:1.1rem; font-weight:600; color:#68D391; margin-bottom:0.3rem;">📱 Android Development Detected</div>
                            <div style="color:#A0AEC0; font-size:0.85rem;">Our analysis says you are looking for <b style="color:#fff;">Android App Development</b> jobs.</div>
                        </div>
                        """, unsafe_allow_html=True)
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">🚀</span> Adding these skills will boost your chances of getting an Android Dev job!</div>''',unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break
                    elif i.lower() in ios_keyword:
                        reco_field = 'IOS Development'
                        st.markdown("""
                        <div class="glass-card" style="border-left: 3px solid #F6AD55;">
                            <div style="font-size:1.1rem; font-weight:600; color:#FDCB6E; margin-bottom:0.3rem;">🍎 iOS Development Detected</div>
                            <div style="color:#A0AEC0; font-size:0.85rem;">Our analysis says you are looking for <b style="color:#fff;">iOS App Development</b> jobs.</div>
                        </div>
                        """, unsafe_allow_html=True)
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">🚀</span> Adding these skills will boost your chances of getting an iOS Dev job!</div>''',unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break
                    elif i.lower() in uiux_keyword:
                        reco_field = 'UI-UX Development'
                        st.markdown("""
                        <div class="glass-card" style="border-left: 3px solid #FF6584;">
                            <div style="font-size:1.1rem; font-weight:600; color:#FF7675; margin-bottom:0.3rem;">🎨 UI/UX Design Detected</div>
                            <div style="color:#A0AEC0; font-size:0.85rem;">Our analysis says you are looking for <b style="color:#fff;">UI/UX Development</b> jobs.</div>
                        </div>
                        """, unsafe_allow_html=True)
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">🚀</span> Adding these skills will boost your chances of getting a UI/UX job!</div>''',unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break
                    elif i.lower() in n_any:
                        reco_field = 'NA'
                        st.markdown("""
                        <div class="glass-card" style="border-left: 3px solid #718096;">
                            <div style="font-size:1.1rem; font-weight:600; color:#A0AEC0; margin-bottom:0.3rem;">⚠️ Limited Field Support</div>
                            <div style="color:#A0AEC0; font-size:0.85rem;">Currently our tool recommends for <b style="color:#fff;">Data Science, Web, Android, iOS and UI/UX</b> only.</div>
                        </div>
                        """, unsafe_allow_html=True)
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Currently No Recommendations',value=recommended_skills,key = '6')
                        st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">📌</span> Support for more fields coming in future updates!</div>''',unsafe_allow_html=True)
                        rec_course = "Sorry! Not Available for this Field"
                        break
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">🥂</div>
                        <div>
                            <div class="text">Resume Tips & Ideas</div>
                            <div class="subtext">Make your resume stand out — here's what you're doing right (and what to improve)</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                resume_score = 0
                if 'Objective' or 'Summary' in resume_text:
                    resume_score = resume_score+6
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Awesome! You have an Objective/Summary section.</div>''',unsafe_allow_html=True)                
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add a career objective — it gives recruiters your career intention.</div>''',unsafe_allow_html=True)
                if 'Education' or 'School' or 'College'  in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Awesome! Education details are included.</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Education — it shows your qualification level to recruiters.</div>''',unsafe_allow_html=True)
                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Great! Work Experience section is present.</div>''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Great! Work Experience section is present.</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Experience — it helps you stand out from the crowd.</div>''',unsafe_allow_html=True)
                if 'INTERNSHIPS'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Nice! Internships are listed.</div>''',unsafe_allow_html=True)
                elif 'INTERNSHIP'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Nice! Internships are listed.</div>''',unsafe_allow_html=True)
                elif 'Internships'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Nice! Internships are listed.</div>''',unsafe_allow_html=True)
                elif 'Internship'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Nice! Internships are listed.</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Internships — real-world experience matters!</div>''',unsafe_allow_html=True)
                if 'SKILLS'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Skills section is present — recruiters love this!</div>''',unsafe_allow_html=True)
                elif 'SKILL'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Skills section is present — recruiters love this!</div>''',unsafe_allow_html=True)
                elif 'Skills'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Skills section is present — recruiters love this!</div>''',unsafe_allow_html=True)
                elif 'Skill'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Skills section is present — recruiters love this!</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add a Skills section — it's one of the most scanned sections!</div>''',unsafe_allow_html=True)
                if 'HOBBIES' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Hobbies added — shows personality!</div>''',unsafe_allow_html=True)
                elif 'Hobbies' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Hobbies added — shows personality!</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Hobbies — it helps recruiters gauge cultural fit.</div>''',unsafe_allow_html=True)
                if 'INTERESTS'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Interests section included — great!</div>''',unsafe_allow_html=True)
                elif 'Interests'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Interests section included — great!</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Interests — shows you're well-rounded beyond just work.</div>''',unsafe_allow_html=True)
                if 'ACHIEVEMENTS' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Achievements listed — shows you're capable!</div>''',unsafe_allow_html=True)
                elif 'Achievements' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Achievements listed — shows you're capable!</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Achievements — proves you're capable for the role.</div>''',unsafe_allow_html=True)
                if 'CERTIFICATIONS' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Certifications included — shows specialization!</div>''',unsafe_allow_html=True)
                elif 'Certifications' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Certifications included — shows specialization!</div>''',unsafe_allow_html=True)
                elif 'Certification' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Certifications included — shows specialization!</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Certifications — proves specialized knowledge.</div>''',unsafe_allow_html=True)
                if 'PROJECTS' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Projects included — the most impactful section!</div>''',unsafe_allow_html=True)
                elif 'PROJECT' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Projects included — the most impactful section!</div>''',unsafe_allow_html=True)
                elif 'Projects' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Projects included — the most impactful section!</div>''',unsafe_allow_html=True)
                elif 'Project' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<div class="tip-card tip-success"><span class="tip-icon">✅</span> Projects included — the most impactful section!</div>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<div class="tip-card tip-missing"><span class="tip-icon">➖</span> Add Projects — this is the #1 thing recruiters look for!</div>''',unsafe_allow_html=True)
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">📝</div>
                        <div>
                            <div class="text">Resume Score</div>
                            <div class="subtext">Based on key resume sections and keywords</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background: linear-gradient(90deg, #6C63FF, #00D2FF) !important;
                            border-radius: 50px !important;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.markdown(f"""
                <div class="glass-card" style="text-align:center; padding:1.5rem;">
                    <div style="font-size:3rem; font-weight:800; 
                        background: linear-gradient(135deg, #6C63FF, #00D2FF);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{score}/100</div>
                    <div style="color:#A0AEC0; font-size:0.85rem; margin-top:0.3rem;">Your Resume Writing Score</div>
                </div>
                """, unsafe_allow_html=True)
                st.info("💡 **Note:** This score is calculated based on the content and key sections present in your resume.")
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)
                insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">🎬</div>
                        <div>
                            <div class="text">Bonus: Resume Writing Tips Video</div>
                            <div class="subtext">Watch expert advice on crafting the perfect resume</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">🎯</div>
                        <div>
                            <div class="text">Bonus: Interview Preparation Video</div>
                            <div class="subtext">Ace your next interview with these proven strategies</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)
                st.balloons()
            else:
                st.error('Something went wrong..')                
    elif choice == '📁  Bulk Upload':
        st.markdown("""
        <div class="glass-card">
            <div class="section-header">
                <div class="icon">📁</div>
                <div>
                    <div class="text">Bulk Resume Upload</div>
                    <div class="subtext">Upload multiple resumes at once and get analysis for all — perfect for recruiters and HR teams</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        pdf_files = st.file_uploader("Choose multiple Resume PDFs", type=["pdf"], accept_multiple_files=True)
        if pdf_files and len(pdf_files) > 0:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 3px solid #6C63FF;">
                <div style="font-size:1.1rem; font-weight:600; color:#A29BFE;">📋 {len(pdf_files)} resume(s) selected for processing</div>
                <div style="color:#A0AEC0; font-size:0.85rem; margin-top:0.3rem;">Fill in your details below and click Process to analyze all resumes.</div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            if st.button('Process All Resumes'):
                sec_token = secrets.token_urlsafe(12)
                host_name = socket.gethostname()
                ip_add = socket.gethostbyname(host_name)
                dev_user = os.getlogin()
                os_name_ver = platform.system() + " " + platform.release()
                try:
                    g = geocoder.ip('me')
                    latlong = g.latlng
                    geolocator = Nominatim(user_agent="http")
                    location = geolocator.reverse(latlong, language='en')
                    address = location.raw['address']
                    cityy = address.get('city', '')
                    statee = address.get('state', '')
                    countryy = address.get('country', '')
                except:
                    latlong = None
                    cityy = ''
                    statee = ''
                    countryy = ''
                city = cityy
                state = statee
                country = countryy
                all_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                for idx, pdf_file in enumerate(pdf_files):
                    status_text.text(f"Processing resume {idx+1} of {len(pdf_files)}: {pdf_file.name}")
                    progress_bar.progress((idx) / len(pdf_files))
                    try:
                        save_image_path = './Uploaded_Resumes/' + pdf_file.name
                        pdf_name = pdf_file.name
                        with open(save_image_path, "wb") as f:
                            f.write(pdf_file.getbuffer())
                        resume_data = ResumeParser(save_image_path).get_extracted_data()
                        if resume_data:
                            resume_text = pdf_reader(save_image_path)
                            cand_level = ''
                            if resume_data['no_of_pages'] and resume_data['no_of_pages'] < 1:
                                cand_level = "NA"
                            elif any(kw in resume_text for kw in ['INTERNSHIP', 'INTERNSHIPS', 'Internship', 'Internships']):
                                cand_level = "Intermediate"
                            elif any(kw in resume_text for kw in ['EXPERIENCE', 'WORK EXPERIENCE', 'Experience', 'Work Experience']):
                                cand_level = "Experienced"
                            else:
                                cand_level = "Fresher"
                            ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                            web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                            android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                            ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                            uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                            reco_field = 'NA'
                            recommended_skills = []
                            rec_course = ''
                            for i in (resume_data['skills'] or []):
                                if i.lower() in ds_keyword:
                                    reco_field = 'Data Science'
                                    recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                                    break
                                elif i.lower() in web_keyword:
                                    reco_field = 'Web Development'
                                    recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                                    break
                                elif i.lower() in android_keyword:
                                    reco_field = 'Android Development'
                                    recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','SDK','SQLite']
                                    break
                                elif i.lower() in ios_keyword:
                                    reco_field = 'IOS Development'
                                    recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                                    break
                                elif i.lower() in uiux_keyword:
                                    reco_field = 'UI-UX Development'
                                    recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                                    break
                            resume_score = 0
                            if 'Objective' in resume_text or 'Summary' in resume_text:
                                resume_score += 6
                            if any(kw in resume_text for kw in ['Education', 'School', 'College']):
                                resume_score += 12
                            if any(kw in resume_text for kw in ['EXPERIENCE', 'Experience']):
                                resume_score += 16
                            if any(kw in resume_text for kw in ['INTERNSHIPS', 'INTERNSHIP', 'Internships', 'Internship']):
                                resume_score += 6
                            if any(kw in resume_text for kw in ['SKILLS', 'SKILL', 'Skills', 'Skill']):
                                resume_score += 7
                            if any(kw in resume_text for kw in ['HOBBIES', 'Hobbies']):
                                resume_score += 4
                            if any(kw in resume_text for kw in ['INTERESTS', 'Interests']):
                                resume_score += 5
                            if any(kw in resume_text for kw in ['ACHIEVEMENTS', 'Achievements']):
                                resume_score += 13
                            if any(kw in resume_text for kw in ['CERTIFICATIONS', 'Certifications', 'Certification']):
                                resume_score += 12
                            if any(kw in resume_text for kw in ['PROJECTS', 'PROJECT', 'Projects', 'Project']):
                                resume_score += 19
                            ts = time.time()
                            cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                            cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                            timestamp = str(cur_date + '_' + cur_time)
                            insert_data(
                                str(sec_token), str(ip_add), host_name, dev_user, os_name_ver,
                                str(latlong), city, state, country,

                                resume_data.get('name', 'N/A') or 'N/A',
                                resume_data.get('email', 'N/A') or 'N/A',
                                resume_data.get('mobile_number', 'N/A') or 'N/A',

                                resume_data.get('name', 'N/A') or 'N/A',
                                resume_data.get('email', 'N/A') or 'N/A',

                                str(resume_score), timestamp,
                                str(resume_data.get('no_of_pages', 'N/A')),
                                reco_field, cand_level,
                                str(resume_data.get('skills', [])),
                                str(recommended_skills), str(rec_course), pdf_name
                            )
                            all_results.append({
                                'File Name': pdf_name,
                                'Name': resume_data.get('name', 'N/A') or 'N/A',
                                'Email': resume_data.get('email', 'N/A') or 'N/A',
                                'Contact': resume_data.get('mobile_number', 'N/A') or 'N/A',
                                'Degree': str(resume_data.get('degree', 'N/A') or 'N/A'),
                                'Pages': resume_data.get('no_of_pages', 'N/A'),
                                'Skills': ', '.join(resume_data.get('skills', []) or []),
                                'Experience Level': cand_level,
                                'Predicted Field': reco_field,
                                'Resume Score': resume_score,
                                'Recommended Skills': ', '.join(recommended_skills) if recommended_skills else 'N/A',
                            })
                        else:
                            all_results.append({
                                'File Name': pdf_name,
                                'Name': 'Parse Error',
                                'Email': 'N/A', 'Contact': 'N/A', 'Degree': 'N/A',
                                'Pages': 'N/A', 'Skills': 'N/A',
                                'Experience Level': 'N/A', 'Predicted Field': 'N/A',
                                'Resume Score': 'N/A', 'Recommended Skills': 'N/A',
                            })
                    except Exception as e:
                        all_results.append({
                            'File Name': pdf_file.name,
                            'Name': 'Error',
                            'Email': str(e), 'Contact': 'N/A', 'Degree': 'N/A',
                            'Pages': 'N/A', 'Skills': 'N/A',
                            'Experience Level': 'N/A', 'Predicted Field': 'N/A',
                            'Resume Score': 'N/A', 'Recommended Skills': 'N/A',
                        })
                progress_bar.progress(1.0)
                status_text.text("All resumes processed!")
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">📊</div>
                        <div>
                            <div class="text">Bulk Upload Results</div>
                            <div class="subtext">Complete analysis of all uploaded resumes</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                results_df = pd.DataFrame(all_results)
                st.dataframe(results_df)
                st.markdown(f'<div class="download-btn">', unsafe_allow_html=True)
                st.markdown(get_csv_download_link(results_df, 'Bulk_Resume_Results.csv', '⬇️  Download Full Report (CSV)'), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.success(f"🎉 **Successfully processed {len(all_results)} resume(s)!** All data has been saved to the database.")
                st.balloons()
        elif pdf_files is not None and len(pdf_files) == 0:
            st.info("No files selected yet. Please upload one or more PDF resumes.")
    elif choice == '💬  Feedback':   
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date+'_'+cur_time)
        st.markdown("""
        <div class="glass-card" style="background: linear-gradient(135deg, rgba(108,99,255,0.12) 0%, rgba(0,210,255,0.08) 50%, rgba(255,101,132,0.08) 100%) !important;">
            <div style="text-align:center; padding: 0.5rem 0;">
                <div style="font-size: 3.5rem; margin-bottom: 0.4rem;">💬</div>
                <h2 style="font-size:1.8rem; font-weight:800; margin:0;
                    background: linear-gradient(135deg, #6C63FF, #00D2FF, #FF6584);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text;">Share Your Feedback</h2>
                <p style="color:#A0AEC0; font-size:0.95rem; margin-top:0.3rem;">
                    Help us improve the AI Resume Analyzer with your suggestions and ratings
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        query_fb = 'select * from user_feedback'
        try:
            plotfeed_data = pd.read_sql(query_fb, connection)
            plotfeed_data['feed_score'] = pd.to_numeric(plotfeed_data['feed_score'], errors='coerce')
            total_fb = len(plotfeed_data)
            avg_score = round(plotfeed_data['feed_score'].mean(), 1) if total_fb > 0 else 0
            star_display = '⭐' * int(round(avg_score)) if total_fb > 0 else '—'
        except:
            total_fb = 0
            avg_score = 0
            star_display = '—'
            plotfeed_data = pd.DataFrame()
        st.markdown(f"""
        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1rem; margin-bottom:1.5rem;">
            <div class="stat-badge">
                <div class="stat-icon">📝</div>
                <div class="stat-value">{total_fb}</div>
                <div class="stat-label">Total Responses</div>
            </div>
            <div class="stat-badge">
                <div class="stat-icon">⭐</div>
                <div class="stat-value">{avg_score}/5</div>
                <div class="stat-label">Average Rating</div>
            </div>
            <div class="stat-badge">
                <div class="stat-icon">🏆</div>
                <div class="stat-value">{star_display}</div>
                <div class="stat-label">User Satisfaction</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card" style="padding-bottom:0; margin-bottom:2rem;">
            <div class="section-header" style="margin-bottom:1rem;">
                <div class="icon">✍️</div>
                <div>
                    <div class="text">Write a Review</div>
                    <div class="subtext">Fill in the form below to submit your feedback</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("my_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                feed_name = st.text_input('Name', placeholder='Your Name')
            with fc2:
                feed_email = st.text_input('Email', placeholder='your@email.com')
            feed_score = st.slider('How would you rate us?', 1, 5, 5,
                help='1 = Poor, 2 = Fair, 3 = Good, 4 = Very Good, 5 = Excellent')
            score_labels = {1:'😞 Poor', 2:'😐 Fair', 3:'🙂 Good', 4:'😊 Very Good', 5:'🌟 Excellent'}
            st.caption(f"**{'⭐' * feed_score}{'☆' * (5-feed_score)}** — {score_labels[feed_score]}")
            comments = st.text_area('Your Comments', placeholder='Tell us what you liked or what we can improve...', height=100)
            Timestamp = timestamp        
            fcol_btn, fcol_empty = st.columns([1, 2])
            with fcol_btn:
                submitted = st.form_submit_button("🚀  Submit Feedback", use_container_width=True)
            if submitted:
                if feed_name and feed_email:
                    insertf_data(feed_name, feed_email, feed_score, comments, Timestamp)    
                    st.success("🎉 Thanks! Your feedback was recorded successfully.") 
                    st.balloons()
                else:
                    st.warning("⚠️ Please fill in your Name and Email before submitting.")
        query = 'select * from user_feedback'        
        plotfeed_data = pd.read_sql(query, connection)                        
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()
        st.markdown("""
        <div class="glass-card" style="margin-top:1.5rem;">
            <div class="section-header">
                <div class="icon">📊</div>
                <div>
                    <div class="text">Rating Distribution</div>
                    <div class="subtext">Visual breakdown of all user ratings</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if not plotfeed_data.empty:
            pie_col, bar_col = st.columns(2)
            with pie_col:
                fig = px.pie(values=values, names=labels, 
                    title="Rating Share", 
                    color_discrete_sequence=px.colors.sequential.Aggrnyl,
                    hole=0.45)
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#A0AEC0', title_font_color='#fff',
                    modebar_bgcolor='rgba(26,29,41,0.9)', modebar_color='#A0AEC0',
                    modebar_activecolor='#6C63FF',
                    margin=dict(l=10, r=10, t=50, b=10),
                    legend=dict(font=dict(color='#A0AEC0')),
                )
                fig.update_traces(textinfo='percent+label', textfont_size=13)
                st.plotly_chart(fig, use_container_width=True)
            with bar_col:
                st.markdown("##### Rating Breakdown")
                for score_val in sorted(plotfeed_data.feed_score.unique(), reverse=True):
                    count = len(plotfeed_data[plotfeed_data.feed_score == score_val])
                    total = len(plotfeed_data)
                    pct = round(count/total*100, 1)
                    bar_width = max(pct, 5)
                    star_str = '⭐' * int(score_val)
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.7rem; padding:0.5rem 0.8rem;
                        background:rgba(26,29,41,0.5); border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
                        <span style="color:#fff; font-size:0.9rem; min-width:90px;">{star_str}</span>
                        <div style="flex:1; background:rgba(255,255,255,0.05); border-radius:50px; height:10px; overflow:hidden;">
                            <div style="width:{bar_width}%; height:100%;
                                background: linear-gradient(90deg, #6C63FF, #00D2FF);
                                border-radius:50px;"></div>
                        </div>
                        <span style="color:#A0AEC0; font-size:0.8rem; min-width:70px; text-align:right;">
                            {count} ({pct}%)
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📭 No feedback data available yet. Be the first to rate!")
        cursor.execute('select feed_name, comments, feed_score, timestamp from user_feedback order by timestamp desc')
        plfeed_cmt_data = cursor.fetchall()
        st.markdown("""
        <div class="glass-card" style="margin-top:1.5rem;">
            <div class="section-header">
                <div class="icon">🗨️</div>
                <div>
                    <div class="text">What Users Are Saying</div>
                    <div class="subtext">Recent comments from the community</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if plfeed_cmt_data:
            for row in plfeed_cmt_data[:10]:  # show latest 10
                fb_name = row[0] if row[0] else 'Anonymous'
                fb_comment = row[1] if row[1] else 'No comment provided'
                fb_score = row[2] if row[2] else 5
                fb_time = row[3] if row[3] else ''
                fb_stars = '⭐' * int(fb_score)
                fb_initial = fb_name[0].upper() if fb_name else '?'
                st.markdown(f"""
                <div style="display:flex; gap:1rem; padding:1.2rem; margin-bottom:0.8rem;
                    background:rgba(26,29,41,0.6); border:1px solid rgba(255,255,255,0.05);
                    border-radius:12px; transition: all 0.2s;">
                    <div style="width:44px; height:44px; border-radius:50%;
                        background: linear-gradient(135deg, #6C63FF, #00D2FF);
                        display:flex; align-items:center; justify-content:center;
                        font-weight:700; font-size:1rem; color:white; flex-shrink:0;">
                        {fb_initial}
                    </div>
                    <div style="flex:1;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
                            <span style="font-weight:600; color:#fff; font-size:0.95rem;">{fb_name}</span>
                            <span style="color:#718096; font-size:0.75rem;">{fb_time}</span>
                        </div>
                        <div style="color:#A0AEC0; font-size:0.85rem; margin-bottom:0.4rem; line-height:1.5;">{fb_comment}</div>
                        <div style="font-size:0.8rem;">{fb_stars}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            if len(plfeed_cmt_data) > 10:
                st.caption(f"Showing latest 10 of {len(plfeed_cmt_data)} comments")
        else:
            st.info("💬 No comments yet. Share your thoughts above!")
    elif choice == 'ℹ️  About':   
        st.markdown("""
        <div class="about-hero">
            <div style="font-size:3rem; margin-bottom:0.5rem;">🤖</div>
            <h2>AI Resume Analyzer</h2>
            <p style="color:#A0AEC0; font-size:1rem; margin-bottom:0;">
                Smart resume parsing, skill recommendations & career insights powered by NLP
            </p>
        </div>
        <div class="glass-card">
            <div class="section-header">
                <div class="icon">📖</div>
                <div>
                    <div class="text">About The Tool</div>
                    <div class="subtext">What it does and how it works</div>
                </div>
            </div>
            <p style="color:#A0AEC0; line-height:1.7; font-size:0.95rem;">
                A powerful tool that parses information from resumes using natural language processing (NLP), 
                extracts key skills and experience, clusters them onto relevant job sectors, and provides 
                personalized recommendations, predictions, and analytics to job applicants based on keyword matching.
            </p>
        </div>
        <div class="feature-grid">
            <div class="feature-item">
                <div class="feat-icon">📄</div>
                <div class="feat-title">Resume Parsing</div>
                <div class="feat-desc">Extracts name, email, skills, degree, and experience using advanced NLP</div>
            </div>
            <div class="feature-item">
                <div class="feat-icon">🎯</div>
                <div class="feat-title">Job Prediction</div>
                <div class="feat-desc">Predicts your ideal field — Data Science, Web, Android, iOS, or UI/UX</div>
            </div>
            <div class="feature-item">
                <div class="feat-icon">💡</div>
                <div class="feat-title">Skill Recommendations</div>
                <div class="feat-desc">Suggests skills to boost your resume based on your current profile</div>
            </div>
            <div class="feature-item">
                <div class="feat-icon">📊</div>
                <div class="feat-title">Resume Score</div>
                <div class="feat-desc">Scores your resume out of 100 based on key sections and completeness</div>
            </div>
            <div class="feature-item">
                <div class="feat-icon">🎓</div>
                <div class="feat-title">Course Suggestions</div>
                <div class="feat-desc">Recommends courses and certifications relevant to your career path</div>
            </div>
            <div class="feature-item">
                <div class="feat-icon">📁</div>
                <div class="feat-title">Bulk Upload</div>
                <div class="feat-desc">Process multiple resumes at once — perfect for recruiters and HR teams</div>
            </div>
            <div class="feature-item">
                <div class="feat-icon">📈</div>
                <div class="feat-title">Admin Analytics</div>
                <div class="feat-desc">Comprehensive pie charts and data views for all user submissions</div>
            </div>
            <div class="feature-item">
                <div class="feat-icon">💬</div>
                <div class="feat-title">Feedback System</div>
                <div class="feat-desc">Users can rate and comment to help improve the tool continuously</div>
            </div>
        </div>
        <div class="glass-card" style="margin-top:1.5rem;">
            <div class="section-header">
                <div class="icon">🚀</div>
                <div>
                    <div class="text">How to Use</div>
                    <div class="subtext">Simple steps to get started</div>
                </div>
            </div>
            <div style="color:#A0AEC0; line-height:1.8; font-size:0.9rem;">
                <div style="margin-bottom:0.8rem;">
                    <span style="color:#A29BFE; font-weight:600;">👤 User</span><br/>
                    Select <b style="color:#fff;">User</b> from the navigation menu → Fill in your details → Upload your resume as PDF → Get instant analysis, recommendations, and score.
                </div>
                <div style="margin-bottom:0.8rem;">
                    <span style="color:#74B9FF; font-weight:600;">📁 Bulk Upload</span><br/>
                    Select <b style="color:#fff;">Bulk Upload</b> → Upload multiple PDF resumes → Process all at once → Download the complete report.
                </div>
                <div style="margin-bottom:0.8rem;">
                    <span style="color:#68D391; font-weight:600;">💬 Feedback</span><br/>
                    Rate the tool from 1-5 stars and share your thoughts to help us improve.
                </div>
                <div>
                    <span style="color:#FDCB6E; font-weight:600;">🔐 Admin</span><br/>
                    Use <code style="background:rgba(108,99,255,0.2); padding:0.2rem 0.5rem; border-radius:4px; color:#A29BFE;">admin</code> as username and 
                    <code style="background:rgba(108,99,255,0.2); padding:0.2rem 0.5rem; border-radius:4px; color:#A29BFE;">admin@resume-analyzer</code> as password to access the full analytics dashboard.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:2rem 0 0.5rem 0;">
            <div style="width:80px; height:80px; border-radius:50%; margin:0 auto 1rem;
                background: linear-gradient(135deg, rgba(108,99,255,0.2), rgba(0,210,255,0.15));
                border: 2px solid rgba(108,99,255,0.3);
                display:flex; align-items:center; justify-content:center;
                box-shadow: 0 0 30px rgba(108,99,255,0.2);">
                <span style="font-size:2.5rem;">🔐</span>
            </div>
            <h2 style="font-size:1.8rem; font-weight:800; margin:0;
                background: linear-gradient(135deg, #6C63FF, #00D2FF);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text;">Admin Dashboard</h2>
            <p style="color:#A0AEC0; font-size:0.9rem; margin-top:0.3rem;">
                Sign in to access analytics, user data, and feedback reports
            </p>
        </div>
        """, unsafe_allow_html=True)
        col_l, col_m, col_r = st.columns([1, 1.5, 1])
        with col_m:
            st.markdown("""
            <div style="background:rgba(26,29,41,0.6); border:1px solid rgba(255,255,255,0.08);
                border-radius:16px; padding:1.8rem; margin-top:0.5rem;">
            </div>
            """, unsafe_allow_html=True)
            ad_user = st.text_input("Username", placeholder="Enter admin username")
            ad_password = st.text_input("Password", type='password', placeholder="Enter password")
            login_clicked = st.button('🔑  Login to Dashboard', use_container_width=True)
        if login_clicked:
            if ad_user == 'admin' and ad_password == 'admin@resume-analyzer':
                cursor.execute('''SELECT ID, ip_add, resume_score, Predicted_Field, User_level, city, state, country from user_data''')
                datanalys = cursor.fetchall()
                plot_data = pd.DataFrame(datanalys, columns=['Idt', 'IP_add', 'resume_score', 'Predicted_Field', 'User_Level', 'City', 'State', 'Country'])
                total_users = plot_data.Idt.count()
                plot_data['resume_score'] = pd.to_numeric(plot_data['resume_score'], errors='coerce')
                avg_score = round(plot_data['resume_score'].mean(), 1) if total_users > 0 and not plot_data['resume_score'].dropna().empty else 0
                unique_fields = plot_data['Predicted_Field'].nunique() if total_users > 0 else 0
                try:
                    cursor.execute('SELECT feed_score from user_feedback')
                    fb_scores = [int(r[0]) for r in cursor.fetchall() if r[0] is not None]
                    total_feedback = len(fb_scores)
                    avg_fb = round(sum(fb_scores)/len(fb_scores), 1) if fb_scores else 0
                except:
                    total_feedback = 0
                    avg_fb = 0
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(72,187,120,0.12), rgba(108,99,255,0.1));
                    border:1px solid rgba(72,187,120,0.25); border-radius:16px;
                    padding:1.5rem 2rem; margin:1.5rem 0; display:flex; align-items:center; gap:1rem;">
                    <div style="font-size:2.5rem;">🎉</div>
                    <div>
                        <div style="font-size:1.2rem; font-weight:700; color:#48BB78;">Welcome back, Admin!</div>
                        <div style="color:#A0AEC0; font-size:0.9rem; margin-top:0.2rem;">
                            <b style="color:#fff;">{total_users}</b> users have used the analyzer so far — here's your complete overview.
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:1rem; margin-bottom:2rem;">
                    <div style="background: linear-gradient(135deg, rgba(108,99,255,0.12), rgba(108,99,255,0.05));
                        border:1px solid rgba(108,99,255,0.25); border-radius:14px; padding:1.3rem; text-align:center;">
                        <div style="font-size:1.8rem; margin-bottom:0.3rem;">👥</div>
                        <div style="font-size:1.6rem; font-weight:800; color:#A29BFE;">{total_users}</div>
                        <div style="font-size:0.72rem; font-weight:600; color:#718096; text-transform:uppercase; letter-spacing:0.05em;">Total Users</div>
                    </div>
                    <div style="background: linear-gradient(135deg, rgba(0,210,255,0.12), rgba(0,210,255,0.05));
                        border:1px solid rgba(0,210,255,0.25); border-radius:14px; padding:1.3rem; text-align:center;">
                        <div style="font-size:1.8rem; margin-bottom:0.3rem;">📊</div>
                        <div style="font-size:1.6rem; font-weight:800; color:#74B9FF;">{avg_score}</div>
                        <div style="font-size:0.72rem; font-weight:600; color:#718096; text-transform:uppercase; letter-spacing:0.05em;">Avg Score</div>
                    </div>
                    <div style="background: linear-gradient(135deg, rgba(255,101,132,0.12), rgba(255,101,132,0.05));
                        border:1px solid rgba(255,101,132,0.25); border-radius:14px; padding:1.3rem; text-align:center;">
                        <div style="font-size:1.8rem; margin-bottom:0.3rem;">🎯</div>
                        <div style="font-size:1.6rem; font-weight:800; color:#FF6584;">{unique_fields}</div>
                        <div style="font-size:0.72rem; font-weight:600; color:#718096; text-transform:uppercase; letter-spacing:0.05em;">Fields Covered</div>
                    </div>
                    <div style="background: linear-gradient(135deg, rgba(72,187,120,0.12), rgba(72,187,120,0.05));
                        border:1px solid rgba(72,187,120,0.25); border-radius:14px; padding:1.3rem; text-align:center;">
                        <div style="font-size:1.8rem; margin-bottom:0.3rem;">💬</div>
                        <div style="font-size:1.6rem; font-weight:800; color:#68D391;">{total_feedback}</div>
                        <div style="font-size:0.72rem; font-weight:600; color:#718096; text-transform:uppercase; letter-spacing:0.05em;">Feedback Received</div>
                    </div>
                    <div style="background: linear-gradient(135deg, rgba(246,173,85,0.12), rgba(246,173,85,0.05));
                        border:1px solid rgba(246,173,85,0.25); border-radius:14px; padding:1.3rem; text-align:center;">
                        <div style="font-size:1.8rem; margin-bottom:0.3rem;">⭐</div>
                        <div style="font-size:1.6rem; font-weight:800; color:#F6AD55;">{avg_fb}/5</div>
                        <div style="font-size:0.72rem; font-weight:600; color:#718096; text-transform:uppercase; letter-spacing:0.05em;">Avg Rating</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                cursor.execute('''SELECT ID, sec_token, ip_add, act_name, act_mail, act_mob, Predicted_Field, Timestamp, Name, Email_ID, resume_score, Page_no, pdf_name, User_level, Actual_skills, Recommended_skills, Recommended_courses, city, state, country, latlong, os_name_ver, host_name, dev_user from user_data''')
                data = cursor.fetchall()                
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <div class="icon">👥</div>
                        <div>
                            <div class="text">User Submissions</div>
                            <div class="subtext">Complete dataset of all user resume analyses</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                df = pd.DataFrame(data, columns=['ID', 'Token', 'IP Address', 'Name', 'Mail', 'Mobile Number', 'Predicted Field', 'Timestamp',
                                                 'Predicted Name', 'Predicted Mail', 'Resume Score', 'Total Page',  'File Name',   
                                                 'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course',
                                                 'City', 'State', 'Country', 'Lat Long', 'Server OS', 'Server Name', 'Server User',])
                display_cols = ['ID', 'Name', 'Mail', 'Mobile Number', 'Predicted Field', 'User Level',
                                'Resume Score', 'Actual Skills', 'Recommended Skills',
                                'City', 'State', 'Country', 'Timestamp', 'File Name']
                df_display = df[[c for c in display_cols if c in df.columns]].copy()
                df_display['Resume Score'] = pd.to_numeric(df_display['Resume Score'], errors='coerce').fillna(0).astype(int)
                df_display['Timestamp'] = pd.to_datetime(df_display['Timestamp'], errors='coerce')
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    height=420,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.NumberColumn(
                            "ID", width="small", format="%d"
                        ),
                        "Name": st.column_config.TextColumn(
                            "👤  Name", width="medium"
                        ),
                        "Mail": st.column_config.TextColumn(
                            "📧  Email", width="medium"
                        ),
                        "Mobile Number": st.column_config.TextColumn(
                            "📱  Mobile", width="small"
                        ),
                        "Predicted Field": st.column_config.TextColumn(
                            "🎯  Field", width="medium"
                        ),
                        "User Level": st.column_config.TextColumn(
                            "📊  Level", width="small"
                        ),
                        "Resume Score": st.column_config.ProgressColumn(
                            "⭐  Score",
                            min_value=0, max_value=100,
                            format="%d/100",
                            width="small"
                        ),
                        "Actual Skills": st.column_config.TextColumn(
                            "🛠️  Actual Skills", width="large"
                        ),
                        "Recommended Skills": st.column_config.TextColumn(
                            "💡  Recommended", width="large"
                        ),
                        "City": st.column_config.TextColumn(
                            "🏙️  City", width="small"
                        ),
                        "State": st.column_config.TextColumn(
                            "📍  State", width="small"
                        ),
                        "Country": st.column_config.TextColumn(
                            "🌍  Country", width="small"
                        ),
                        "Timestamp": st.column_config.DatetimeColumn(
                            "🕒  Submitted",
                            format="DD MMM YYYY, HH:mm",
                            width="medium"
                        ),
                        "File Name": st.column_config.TextColumn(
                            "📄  File", width="medium"
                        ),
                    }
                )
                st.markdown('<div class="download-btn" style="margin-top:0.8rem;">', unsafe_allow_html=True)
                st.markdown(get_csv_download_link(df,'User_Data.csv','⬇️  Download Full User Report (CSV)'), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                cursor.execute('''SELECT * from user_feedback''')
                fb_data = cursor.fetchall()
                st.markdown("""
                <div class="glass-card" style="margin-top:1.5rem;">
                    <div class="section-header">
                        <div class="icon">💬</div>
                        <div>
                            <div class="text">Feedback Reports</div>
                            <div class="subtext">All user feedback and ratings collected over time</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                df_fb = pd.DataFrame(fb_data, columns=['ID', 'Name', 'Email', 'Rating', 'Comments', 'Timestamp'])
                df_fb['Rating'] = pd.to_numeric(df_fb['Rating'], errors='coerce').fillna(0).astype(int)
                df_fb['Timestamp'] = pd.to_datetime(df_fb['Timestamp'], errors='coerce')
                st.dataframe(
                    df_fb,
                    use_container_width=True,
                    height=320,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.NumberColumn(
                            "ID", width="small", format="%d"
                        ),
                        "Name": st.column_config.TextColumn(
                            "👤  Name", width="medium"
                        ),
                        "Email": st.column_config.TextColumn(
                            "📧  Email", width="medium"
                        ),
                        "Rating": st.column_config.ProgressColumn(
                            "⭐  Rating",
                            min_value=0, max_value=5,
                            format="%d/5 ⭐",
                            width="small"
                        ),
                        "Comments": st.column_config.TextColumn(
                            "💬  Comments", width="large"
                        ),
                        "Timestamp": st.column_config.DatetimeColumn(
                            "🕒  Submitted",
                            format="DD MMM YYYY, HH:mm",
                            width="medium"
                        ),
                    }
                )
                chart_layout = dict(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#A0AEC0',
                    title_font_color='#fff',
                    title_font_size=14,
                    modebar_bgcolor='rgba(26,29,41,0.9)',
                    modebar_color='#A0AEC0',
                    modebar_activecolor='#6C63FF',
                    margin=dict(l=15, r=15, t=55, b=15),
                    legend=dict(font=dict(color='#A0AEC0', size=11), bgcolor='rgba(0,0,0,0)'),
                )
                query = 'select * from user_feedback'
                plotfeed_data = pd.read_sql(query, connection)                        
                st.markdown("""
                <div class="glass-card" style="margin-top:1.5rem;">
                    <div class="section-header">
                        <div class="icon">📈</div>
                        <div>
                            <div class="text">Analytics Dashboard</div>
                            <div class="subtext">Visual breakdown of all user data — ratings, fields, geography, and more</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                row1_col1, row1_col2 = st.columns(2)
                with row1_col1:
                    labels_fb = plotfeed_data.feed_score.unique()
                    values_fb = plotfeed_data.feed_score.value_counts()
                    fig = px.pie(values=values_fb, names=labels_fb, title="User Ratings Distribution",
                        color_discrete_sequence=px.colors.sequential.Aggrnyl, hole=0.48)
                    fig.update_layout(**chart_layout)
                    fig.update_traces(textinfo='percent+label', textfont_size=12, pull=[0.03]*len(labels_fb))
                    st.plotly_chart(fig, use_container_width=True)
                with row1_col2:
                    if not plot_data.empty:
                        top_fields = plot_data['Predicted_Field'].value_counts().head(5)
                        fig2 = px.bar(x=top_fields.values, y=top_fields.index, orientation='h',
                            title='Top 5 Predicted Fields',
                            color=top_fields.values,
                            color_continuous_scale='Aggrnyl')
                        fig2.update_layout(**chart_layout, showlegend=False,
                            xaxis_title='Count', yaxis_title='',
                            yaxis=dict(autorange='reversed'))
                        fig2.update_traces(textposition='outside', texttemplate='%{x}')
                        st.plotly_chart(fig2, use_container_width=True)
                row2_col1, row2_col2 = st.columns(2)
                with row2_col1:
                    labels_lvl = plot_data.User_Level.unique()
                    values_lvl = plot_data.User_Level.value_counts()
                    fig = px.pie(values=values_lvl, names=labels_lvl, title="Experience Level Split",
                        color_discrete_sequence=px.colors.sequential.RdBu, hole=0.48)
                    fig.update_layout(**chart_layout)
                    fig.update_traces(textinfo='percent+label', textfont_size=12)
                    st.plotly_chart(fig, use_container_width=True)
                with row2_col2:
                    if 'resume_score' in plot_data.columns:
                        fig3 = px.histogram(plot_data, x='resume_score', nbins=15,
                            title='Resume Score Distribution',
                            color_discrete_sequence=['#6C63FF'])
                        fig3.update_layout(**chart_layout,
                            xaxis_title='Score', yaxis_title='Count',
                            bargap=0.1)
                        fig3.update_traces(marker_line=dict(width=1, color='rgba(0,210,255,0.5)'))
                        st.plotly_chart(fig3, use_container_width=True)
                row3_col1, row3_col2 = st.columns(2)
                with row3_col1:
                    labels_city = plot_data.City.unique()[:15]
                    values_city = plot_data.City.value_counts().head(15)
                    fig = px.pie(values=values_city.values, names=values_city.index,
                        title="Top 15 Cities", color_discrete_sequence=px.colors.sequential.Jet, hole=0.48)
                    fig.update_layout(**chart_layout)
                    fig.update_traces(textinfo='percent+label', textfont_size=11)
                    st.plotly_chart(fig, use_container_width=True)
                with row3_col2:
                    top_cities = plot_data['City'].value_counts().head(8)
                    fig4 = px.bar(x=top_cities.index, y=top_cities.values,
                        title='Top 8 Cities by Usage',
                        color=top_cities.values,
                        color_continuous_scale='Jet')
                    fig4.update_layout(**chart_layout, showlegend=False,
                        xaxis_title='City', yaxis_title='Users')
                    fig4.update_traces(textposition='outside', texttemplate='%{y}')
                    st.plotly_chart(fig4, use_container_width=True)
                row4_col1, row4_col2 = st.columns(2)
                with row4_col1:
                    labels_st = plot_data.State.value_counts().head(12)
                    fig = px.pie(values=labels_st.values, names=labels_st.index,
                        title="Usage by State (Top 12)", color_discrete_sequence=px.colors.sequential.PuBu_r, hole=0.48)
                    fig.update_layout(**chart_layout)
                    fig.update_traces(textinfo='percent+label', textfont_size=11)
                    st.plotly_chart(fig, use_container_width=True)
                with row4_col2:
                    labels_ct = plot_data.Country.value_counts().head(12)
                    fig = px.pie(values=labels_ct.values, names=labels_ct.index,
                        title="Usage by Country (Top 12)", color_discrete_sequence=px.colors.sequential.Purpor_r, hole=0.48)
                    fig.update_layout(**chart_layout)
                    fig.update_traces(textinfo='percent+label', textfont_size=11)
                    st.plotly_chart(fig, use_container_width=True)
                try:
                    os_info = platform.system() + ' ' + platform.release()
                    host = socket.gethostname()
                    ip_local = socket.gethostbyname(host)
                except:
                    os_info = 'N/A'
                    host = 'N/A'
                    ip_local = 'N/A'
                st.markdown(f"""
                <div style="background:rgba(26,29,41,0.6); border:1px solid rgba(255,255,255,0.06);
                    border-radius:14px; padding:1.5rem; margin-top:1.5rem;
                    display:grid; grid-template-columns: repeat(4, 1fr); gap:1rem; text-align:center;">
                    <div>
                        <div style="font-size:1.3rem; margin-bottom:0.3rem;">🖥️</div>
                        <div style="color:#718096; font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">Server OS</div>
                        <div style="color:#fff; font-size:0.88rem; font-weight:500;">{os_info}</div>
                    </div>
                    <div>
                        <div style="font-size:1.3rem; margin-bottom:0.3rem;">🌐</div>
                        <div style="color:#718096; font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">Hostname</div>
                        <div style="color:#fff; font-size:0.88rem; font-weight:500;">{host}</div>
                    </div>
                    <div>
                        <div style="font-size:1.3rem; margin-bottom:0.3rem;">📡</div>
                        <div style="color:#718096; font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">Local IP</div>
                        <div style="color:#fff; font-size:0.88rem; font-weight:500;">{ip_local}</div>
                    </div>
                    <div>
                        <div style="font-size:1.3rem; margin-bottom:0.3rem;">🐍</div>
                        <div style="color:#718096; font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">Python</div>
                        <div style="color:#fff; font-size:0.88rem; font-weight:500;">{platform.python_version()}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:rgba(252,129,129,0.1); border:1px solid rgba(252,129,129,0.3);
                    border-radius:12px; padding:1.2rem; margin-top:1rem; text-align:center;">
                    <span style="font-size:1.5rem;">🚫</span>
                    <div style="color:#FC8181; font-weight:600; margin-top:0.3rem;">Invalid Credentials</div>
                    <div style="color:#A0AEC0; font-size:0.85rem;">Please check your username and password and try again.</div>
                </div>
                """, unsafe_allow_html=True)
run()