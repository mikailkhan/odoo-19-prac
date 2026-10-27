# -*- coding: utf-8 -*-
{
    'name': 'UniSphere — University Management System',
    'version': '19.0.4.0.0',
    'category': 'Education/University',
    'summary': 'Mini University Management System for Northstar University of Technology (NUT)',
    'description': """
UniSphere University Management System
======================================
An institutional ERP solution built on Odoo 19 for Northstar University of Technology.

Core Modules:
-------------
- Academic Architecture (Departments, Terms, Courses, Course Sections)
- Student & Faculty Directories with Odoo Contact & User Synchronization
- Course Enrollment with Dynamic Capacity & Prerequisite Validation
- Session-based Attendance Registers
- Continuous Assessments & Term Gradebooks
- Scoped Fee & Challan Billing Ledgers
- Institutional Executive Dashboard
- Dedicated Student Portal Web Experience
- Optional Context-Aware AI Academic Assistant
    """,
    'author': 'Northstar University of Technology / Mikail Khan',
    'website': 'https://github.com/mikailkhan/odoo-19-prac',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'portal',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/department_views.xml',
        'views/academic_term_views.xml',
        'views/course_views.xml',
        'views/faculty_views.xml',
        'views/course_section_views.xml',
        'views/student_views.xml',
        'views/enrollment_views.xml',
        'views/menus.xml',
        'data/demo_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
