import { defineStore } from 'pinia';

export const useSessionStore = defineStore('session', {
  state: () => ({
    role: null, // 'student' | 'teacher' | 'parent' | 'admin'
    user: null
  }),
  actions: {
    setRole(role) {
      this.role = role;
      localStorage.setItem('userRole', role || '');
    },
    setUser(user) {
      this.user = user;
      localStorage.setItem('userData', JSON.stringify(user || null));
    },
    reset() {
      this.role = null;
      this.user = null;
      localStorage.removeItem('userRole');
      localStorage.removeItem('userData');
    },
    initialize() {
      const savedRole = localStorage.getItem('userRole');
      const savedUser = localStorage.getItem('userData');
      
      if (savedRole) {
        this.role = savedRole;
      }
      if (savedUser && savedUser !== 'null') {
        try {
          this.user = JSON.parse(savedUser);
        } catch (error) {
          console.warn('Failed to parse saved user data:', error);
          localStorage.removeItem('userData');
        }
      }
    }
  }
});


