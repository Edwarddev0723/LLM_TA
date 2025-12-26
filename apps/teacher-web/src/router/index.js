import { createRouter, createWebHistory } from 'vue-router';

import RoleSelection from '@/views/RoleSelection.vue';
import Login from '@/views/Login.vue';

import StudentLayout from '@/views/student/StudentLayout.vue';
import StudentDashboard from '@/views/student/StudentDashboard.vue';
import PracticeMode from '@/views/student/PracticeMode.vue';
import TeachingMode from '@/views/student/TeachingMode.vue';
import MistakeClinic from '@/views/student/MistakeClinic.vue';
import ProfileRewards from '@/views/student/ProfileRewards.vue';
import StudentProfileEdit from '@/views/student/StudentProfileEdit.vue';

import TeacherLayout from '@/views/teacher/TeacherLayout.vue';
import TeacherOverview from '@/views/teacher/TeacherOverview.vue';
import TeacherStudentDetail from '@/views/teacher/TeacherStudentDetail.vue';
import TeachingSuggestions from '@/views/teacher/TeachingSuggestions.vue';
import TeacherProfileEdit from '@/views/teacher/TeacherProfileEdit.vue';
import TeacherClassManagement from '@/views/teacher/TeacherClassManagement.vue';
import TeacherImportQuestions from '@/views/teacher/TeacherImportQuestions.vue';

import ParentLayout from '@/views/parent/ParentLayout.vue';
import ParentOverview from '@/views/parent/ParentOverview.vue';
import ParentStudentDetail from '@/views/parent/ParentStudentDetail.vue';
import ParentProfileEdit from '@/views/parent/ParentProfileEdit.vue';

import AdminDashboard from '@/views/AdminDashboard.vue';

const routes = [
  {
    path: '/',
    name: 'login',
    component: Login
  },
  {
    path: '/select-role',
    name: 'role-selection',
    component: RoleSelection
  },
  {
    path: '/student',
    component: StudentLayout,
    children: [
      { path: '', name: 'student-dashboard', component: StudentDashboard },
      { path: 'practice', name: 'student-practice', component: PracticeMode },
      {
        path: 'teaching',
        name: 'student-teaching',
        component: TeachingMode,
        meta: { immersive: true }
      },
      {
        path: 'mistakes',
        name: 'student-mistakes',
        component: MistakeClinic
      },
      {
        path: 'profile',
        name: 'student-profile',
        component: ProfileRewards
      },
      {
        path: 'profile/edit',
        name: 'student-profile-edit',
        component: StudentProfileEdit
      }
    ]
  },
  {
    path: '/teacher',
    component: TeacherLayout,
    children: [
      { path: '', name: 'teacher-overview', component: TeacherOverview },
      {
        path: 'classes',
        name: 'teacher-classes',
        component: TeacherClassManagement
      },
      {
        path: 'import-questions',
        name: 'teacher-import-questions',
        component: TeacherImportQuestions
      },
      {
        path: 'students/:id',
        name: 'teacher-student-detail',
        component: TeacherStudentDetail
      },
      {
        path: 'suggestions',
        name: 'teacher-suggestions',
        component: TeachingSuggestions
      },
      {
        path: 'profile/edit',
        name: 'teacher-profile-edit',
        component: TeacherProfileEdit
      }
    ]
  },
  {
    path: '/parent',
    component: ParentLayout,
    children: [
      { path: '', name: 'parent-overview', component: ParentOverview },
      {
        path: 'students/:id',
        name: 'parent-student-detail',
        component: ParentStudentDetail
      },
      {
        path: 'profile/edit',
        name: 'parent-profile-edit',
        component: ParentProfileEdit
      }
    ]
  },
  {
    path: '/admin',
    name: 'admin-dashboard',
    component: AdminDashboard
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;


