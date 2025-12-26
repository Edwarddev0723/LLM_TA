import { defineStore } from 'pinia';

export const useClassAndRolesStore = defineStore('class-and-roles', {
  state: () => ({
    // 班級列表
    classes: [
      { id: 1, name: '2年3班', teacherId: 'teacher-001', teacherName: '王老師' },
      { id: 2, name: '2年2班', teacherId: 'teacher-002', teacherName: '李老師' },
      { id: 3, name: '2年1班', teacherId: 'teacher-003', teacherName: '陳老師' }
    ],

    // 待審核的註冊申請
    pendingApprovals: [
      {
        id: 1,
        name: '新學生1',
        email: 'student1@example.com',
        role: 'student',
        classId: 1,
        className: '2年3班',
        status: 'pending', // pending, approved, rejected
        createdAt: '2025-12-04',
        reviewedBy: null
      },
      {
        id: 2,
        name: '新家長1',
        email: 'parent1@example.com',
        role: 'parent',
        classId: 1,
        className: '2年3班',
        studentName: '學生名字',
        relationship: '父親',
        status: 'pending',
        createdAt: '2025-12-04',
        reviewedBy: null
      }
    ],

    // 已註冊的用戶及其角色
    registeredUsers: [
      {
        id: 'teacher-001',
        name: '王老師',
        email: 'teacher1@example.com',
        role: 'teacher',
        classId: 1,
        className: '2年3班',
        status: 'approved',
        createdAt: '2025-11-01'
      },
      {
        id: 'student-001',
        name: '張小明',
        email: 'student-001@example.com',
        role: 'student',
        classId: 1,
        className: '2年3班',
        status: 'approved',
        createdAt: '2025-11-15'
      },
      {
        id: 'parent-001',
        name: '張家長',
        email: 'parent-001@example.com',
        role: 'parent',
        classId: 1,
        className: '2年3班',
        studentId: 'student-001',
        studentName: '張小明',
        relationship: '父親',
        status: 'approved',
        createdAt: '2025-11-15'
      }
    ],

    // 管理員用戶
    admins: [
      {
        id: 'admin-001',
        name: '系統管理員',
        email: 'admin@example.com',
        role: 'admin',
        status: 'approved',
        createdAt: '2025-10-01'
      }
    ]
  }),

  getters: {
    // 獲取待審核的項目（按角色）
    getPendingByRole: (state) => (role) => {
      return state.pendingApprovals.filter(item => item.role === role && item.status === 'pending');
    },

    // 獲取某班級的所有審核項目
    getPendingByClass: (state) => (classId) => {
      return state.pendingApprovals.filter(item => item.classId === classId && item.status === 'pending');
    },

    // 獲取某班級的學生
    getStudentsByClass: (state) => (classId) => {
      return state.registeredUsers.filter(
        user => user.role === 'student' && user.classId === classId && user.status === 'approved'
      );
    },

    // 獲取某班級的家長
    getParentsByClass: (state) => (classId) => {
      return state.registeredUsers.filter(
        user => user.role === 'parent' && user.classId === classId && user.status === 'approved'
      );
    },

    // 獲取某班級的教師
    getTeacherByClass: (state) => (classId) => {
      const classInfo = state.classes.find(c => c.id === classId);
      return classInfo ? state.registeredUsers.find(u => u.id === classInfo.teacherId) : null;
    }
  },

  actions: {
    // 添加新班級
    addClass(className, teacherId) {
      const newClass = {
        id: Math.max(...this.classes.map(c => c.id), 0) + 1,
        name: className,
        teacherId: teacherId,
        teacherName: this.registeredUsers.find(u => u.id === teacherId)?.name || '待分配'
      };
      this.classes.push(newClass);
      return newClass;
    },

    // 創建用戶註冊申請
    createRegistration(userData) {
      const newApplication = {
        id: Math.max(...this.pendingApprovals.map(a => a.id), 0) + 1,
        ...userData,
        status: 'pending',
        createdAt: new Date().toISOString().split('T')[0],
        reviewedBy: null
      };
      this.pendingApprovals.push(newApplication);
      return newApplication;
    },

    // 批准註冊申請（老師或管理員審核）
    approveRegistration(applicationId, reviewedByUserId) {
      const application = this.pendingApprovals.find(a => a.id === applicationId);
      if (!application) return false;

      application.status = 'approved';
      application.reviewedBy = reviewedByUserId;

      // 將申請轉換為已註冊用戶
      const newUser = {
        id: `${application.role}-${Math.random().toString(36).substr(2, 9)}`,
        name: application.name,
        email: application.email,
        role: application.role,
        classId: application.classId,
        className: application.className,
        ...(application.role === 'parent' && {
          studentId: application.studentId,
          studentName: application.studentName,
          relationship: application.relationship
        }),
        status: 'approved',
        createdAt: new Date().toISOString().split('T')[0]
      };

      this.registeredUsers.push(newUser);
      return newUser;
    },

    // 拒絕註冊申請
    rejectRegistration(applicationId) {
      const application = this.pendingApprovals.find(a => a.id === applicationId);
      if (!application) return false;

      application.status = 'rejected';
      return true;
    },

    // 更改用戶班級（老師或管理員使用）
    changeUserClass(userId, newClassId) {
      const user = this.registeredUsers.find(u => u.id === userId);
      if (!user) return false;

      // 不允許老師改自己的班級
      if (user.role === 'teacher') return false;

      const newClass = this.classes.find(c => c.id === newClassId);
      user.classId = newClassId;
      user.className = newClass?.name || '未知班級';
      return true;
    },

    // 分配老師給班級（管理員使用）
    assignTeacherToClass(classId, teacherId) {
      const classInfo = this.classes.find(c => c.id === classId);
      const teacher = this.registeredUsers.find(u => u.id === teacherId && u.role === 'teacher');

      if (!classInfo || !teacher) return false;

      classInfo.teacherId = teacherId;
      classInfo.teacherName = teacher.name;

      // 更新老師的班級
      teacher.classId = classId;
      teacher.className = classInfo.name;
      return true;
    },

    // 更新班級資訊（管理員使用）
    updateClass(classId, className, teacherId) {
      const classInfo = this.classes.find(c => c.id === classId);
      if (!classInfo) return false;

      // 更新班級名稱
      if (className) {
        classInfo.name = className;
        // 更新該班級所有用戶的班級名稱
        this.registeredUsers.forEach(user => {
          if (user.classId === classId) {
            user.className = className;
          }
        });
      }

      // 更新班級教師
      if (teacherId !== undefined) {
        const oldTeacher = this.registeredUsers.find(u => u.id === classInfo.teacherId && u.role === 'teacher');
        if (oldTeacher) {
          oldTeacher.classId = null;
          oldTeacher.className = null;
        }

        if (teacherId) {
          const newTeacher = this.registeredUsers.find(u => u.id === teacherId && u.role === 'teacher');
          if (newTeacher) {
            classInfo.teacherId = teacherId;
            classInfo.teacherName = newTeacher.name;
            newTeacher.classId = classId;
            newTeacher.className = classInfo.name;
          }
        } else {
          classInfo.teacherId = null;
          classInfo.teacherName = '待分配';
        }
      }

      return true;
    },

    // 刪除班級（管理員使用）
    deleteClass(classId) {
      const classIndex = this.classes.findIndex(c => c.id === classId);
      if (classIndex === -1) return false;

      // 檢查是否有學生或家長在這個班級
      const hasUsers = this.registeredUsers.some(u => 
        (u.role === 'student' || u.role === 'parent') && u.classId === classId
      );

      if (hasUsers) {
        return false; // 有用戶的班級不能刪除
      }

      // 清除該班級教師的班級資訊
      const teacher = this.registeredUsers.find(u => u.id === this.classes[classIndex].teacherId);
      if (teacher) {
        teacher.classId = null;
        teacher.className = null;
      }

      this.classes.splice(classIndex, 1);
      return true;
    }
  }
});
