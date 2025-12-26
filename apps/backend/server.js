const express = require('express');
const bcrypt = require('bcrypt');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 3001;

// multer 用於文件上傳
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB 限制
  },
  fileFilter: (req, file, cb) => {
    // 只允許圖片文件和 PDF 文件
    if (file.mimetype.startsWith('image/') || file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(new Error('只允許上傳圖片文件和 PDF 文件'));
    }
  }
});

app.use(cors()); // 啟用 CORS
app.use(express.json());
app.use('/uploads', express.static('uploads')); // 提供上傳文件的資料夾

// 取得所有用戶 API
app.get('/api/users', (req, res) => {
  db.query('SELECT id, username, email, role, created_at FROM users', (err, results) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ users: results });
  });
});

// 建立新用戶 API
app.post('/api/users', (req, res) => {
  const { username, email, password_hash, role } = req.body;
  db.query('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
    [username, email, password_hash, role], (err, result) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ id: result.insertId });
  });
});

// 用戶註冊 API
app.post('/api/auth/register', upload.single('idDocument'), async (req, res) => {
  try {
    const { email, password, role, fullName } = req.body;
    const idDocument = req.file;

    // 驗證必填欄位
    if (!email || !password || !role || !fullName) {
      return res.status(400).json({ error: '所有欄位都是必填的' });
    }

    // 驗證角色（不能註冊管理員）
    const allowedRoles = ['student', 'teacher', 'parent'];
    if (!allowedRoles.includes(role)) {
      return res.status(400).json({ error: '無效的角色選擇' });
    }

    // 驗證身份證明文件（只有老師需要）
    if (role === 'teacher' && !idDocument) {
      return res.status(400).json({ error: '老師必須上傳教師證明文件' });
    }

    // 如果不是老師，不需要文件
    const idDocumentPath = role === 'teacher' ? idDocument?.path : null;

    // 檢查郵箱是否已存在
    const [emailResults] = await db.promise().query('SELECT id FROM users WHERE email = ?', [email]);
    if (emailResults.length > 0) {
      return res.status(400).json({ error: '郵箱已存在' });
    }

    // 雜湊密碼
    const saltRounds = 10;
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // 建立新用戶
    const [result] = await db.promise().query(
      'INSERT INTO users (email, password_hash, role, full_name, id_document_path, verification_status) VALUES (?, ?, ?, ?, ?, ?)',
      [email, hashedPassword, role, fullName, idDocumentPath, role === 'teacher' ? 'pending' : 'approved']
    );

    res.status(201).json({
      message: role === 'teacher'
        ? '註冊成功！請等待管理員審核您的教師證明文件。'
        : '註冊成功！您可以立即登入使用系統。',
      user: {
        id: result.insertId,
        email,
        full_name: fullName,
        role,
        verification_status: role === 'teacher' ? 'pending' : 'approved'
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 用戶登入 API
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // 驗證必填欄位
    if (!email || !password) {
      return res.status(400).json({ error: '電子郵件和密碼都是必填的' });
    }

    // 查找用戶
    const [results] = await db.promise().query('SELECT id, email, password_hash, role, full_name, verification_status FROM users WHERE email = ?',
      [email]);

    if (results.length === 0) {
      return res.status(401).json({ error: '電子郵件或密碼錯誤' });
    }

    const user = results[0];

    // 檢查驗證狀態
    if (user.verification_status !== 'approved') {
      return res.status(403).json({ error: '帳戶尚未通過驗證，請等待管理員審核' });
    }

    // 驗證密碼
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    if (!isValidPassword) {
      return res.status(401).json({ error: '電子郵件或密碼錯誤' });
    }

    // 登入成功，返回用戶資訊
    res.json({
      message: '登入成功',
      user: {
        id: user.id,
        email: user.email,
        full_name: user.full_name,
        role: user.role
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 獲取當前用戶資訊 API
app.get('/api/auth/me', async (req, res) => {
  try {
    const userId = req.headers['user-id'];

    if (!userId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    // 查詢用戶資訊
    const [results] = await db.promise().query(
      'SELECT id, email, full_name, role, verification_status, created_at, grade, class, phone, student_name, relationship FROM users WHERE id = ?',
      [userId]
    );

    if (results.length === 0) {
      return res.status(404).json({ error: '用戶不存在' });
    }

    const user = results[0];

    const mappedUser = {
      id: user.id,
      email: user.email,
      name: user.full_name,
      role: user.role,
      verification_status: user.verification_status,
      created_at: user.created_at,
      ...(user.grade && { grade: user.grade }),
      ...(user.class && { class: user.class }),
      ...(user.phone && { phone: user.phone }),
      ...(user.student_name && { studentName: user.student_name }),
      ...(user.relationship && { relationship: user.relationship })
    };

    res.json({
      user: mappedUser
    });
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 更新用戶資訊 API
app.put('/api/auth/me', async (req, res) => {
  try {
    const userId = req.headers['user-id'];

    if (!userId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    const { name, grade, class: userClass, phone, studentName, relationship } = req.body;

    const updateData = {};
    if (name !== undefined) updateData.full_name = name;
    if (grade !== undefined) updateData.grade = grade;
    if (userClass !== undefined) updateData.class = userClass;
    if (phone !== undefined) updateData.phone = phone;
    if (studentName !== undefined) updateData.student_name = studentName;
    if (relationship !== undefined) updateData.relationship = relationship;

    if (Object.keys(updateData).length === 0) {
      return res.status(400).json({ error: '沒有提供要更新的欄位' });
    }

    // UPDATE
    const setClause = Object.keys(updateData).map(key => `${key} = ?`).join(', ');
    const values = Object.values(updateData);
    values.push(userId);

    await db.promise().query(
      `UPDATE users SET ${setClause} WHERE id = ?`,
      values
    );

    // 重新獲取更新後的用戶資料
    const [results] = await db.promise().query(
      'SELECT id, email, full_name, role, verification_status, created_at, grade, class, phone, student_name, relationship FROM users WHERE id = ?',
      [userId]
    );

    if (results.length === 0) {
      return res.status(404).json({ error: '用戶不存在' });
    }

    const user = results[0];

    const mappedUser = {
      id: user.id,
      email: user.email,
      name: user.full_name,
      role: user.role,
      verification_status: user.verification_status,
      created_at: user.created_at,
      ...(user.grade && { grade: user.grade }),
      ...(user.class && { class: user.class }),
      ...(user.phone && { phone: user.phone }),
      ...(user.student_name && { studentName: user.student_name }),
      ...(user.relationship && { relationship: user.relationship })
    };

    res.json({
      message: '用戶資訊已更新',
      user: mappedUser
    });
  } catch (error) {
    console.error('Update user error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 管理員審核用戶 API
app.post('/api/admin/verify-user', async (req, res) => {
  try {
    const { userId, action, adminId } = req.body; // action: 'approve' 或 'reject'

    if (!userId || !action || !adminId) {
      return res.status(400).json({ error: '缺少必要參數' });
    }

    // 檢查管理員權限
    const [adminResults] = await db.promise().query('SELECT role FROM users WHERE id = ?', [adminId]);
    if (adminResults.length === 0 || adminResults[0].role !== 'admin') {
      return res.status(403).json({ error: '無權限執行此操作' });
    }

    // 更新用戶驗證狀態
    const status = action === 'approve' ? 'approved' : 'rejected';
    await db.promise().query(
      'UPDATE users SET verification_status = ?, verified_by = ?, verified_at = NOW() WHERE id = ?',
      [status, adminId, userId]
    );

    res.json({
      message: `用戶${action === 'approve' ? '已通過' : '已被拒絕'}驗證`,
      userId,
      status
    });
  } catch (error) {
    console.error('Verification error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 獲取待審核用戶列表 API
app.get('/api/admin/pending-users', async (req, res) => {
  try {
    const [results] = await db.query(
      'SELECT id, email, full_name, role, id_document_path, created_at FROM users WHERE verification_status = ?',
      ['pending']
    );

    res.json({ pendingUsers: results });
  } catch (error) {
    console.error('Get pending users error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// ===== 老師班級管理 API ===== //

// 獲取老師的班級列表
app.get('/api/teacher/classes', async (req, res) => {
  try {
    const teacherId = req.headers['user-id'];

    if (!teacherId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    const [classes] = await db.query(
      `SELECT c.id, c.class_name, c.description, c.created_at, c.updated_at,
              COUNT(cs.id) as studentCount
       FROM classes c
       LEFT JOIN class_students cs ON c.id = cs.class_id
       WHERE c.teacher_id = ?
       GROUP BY c.id
       ORDER BY c.created_at DESC`,
      [teacherId]
    );

    res.json({ classes });
  } catch (error) {
    console.error('Get classes error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 建立新班級
app.post('/api/teacher/classes', async (req, res) => {
  try {
    const teacherId = req.headers['user-id'];
    const { class_name, description, subject } = req.body;

    if (!teacherId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    if (!class_name) {
      return res.status(400).json({ error: '班級名稱是必填的' });
    }

    const [result] = await db.query(
      'INSERT INTO classes (class_name, description, teacher_id) VALUES (?, ?, ?)',
      [class_name, description || null, teacherId]
    );

    res.status(201).json({
      message: '班級建立成功',
      classId: result.insertId
    });
  } catch (error) {
    console.error('Create class error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 刪除班級
app.delete('/api/teacher/classes/:classId', async (req, res) => {
  try {
    const teacherId = req.headers['user-id'];
    const { classId } = req.params;

    if (!teacherId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    // 驗證老師是否擁有此班級
    const [classResult] = await db.query(
      'SELECT teacher_id FROM classes WHERE id = ?',
      [classId]
    );

    if (classResult.length === 0 || classResult[0].teacher_id !== parseInt(teacherId)) {
      return res.status(403).json({ error: '無權限刪除此班級' });
    }

    await db.query('DELETE FROM classes WHERE id = ?', [classId]);

    res.json({ message: '班級已刪除' });
  } catch (error) {
    console.error('Delete class error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 獲取班級的學生列表
app.get('/api/teacher/classes/:classId/students', async (req, res) => {
  try {
    const teacherId = req.headers['user-id'];
    const { classId } = req.params;

    if (!teacherId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    // 驗證老師是否擁有此班級
    const [classResult] = await db.query(
      'SELECT teacher_id FROM classes WHERE id = ?',
      [classId]
    );

    if (classResult.length === 0 || classResult[0].teacher_id !== parseInt(teacherId)) {
      return res.status(403).json({ error: '無權限訪問此班級' });
    }

    const [students] = await db.query(
      `SELECT u.id, u.email, u.full_name, u.role, cs.joined_at
       FROM class_students cs
       JOIN users u ON cs.student_id = u.id
       WHERE cs.class_id = ?
       ORDER BY cs.joined_at DESC`,
      [classId]
    );

    res.json({ students });
  } catch (error) {
    console.error('Get class students error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 從班級移除學生
app.delete('/api/teacher/classes/:classId/students/:studentId', async (req, res) => {
  try {
    const teacherId = req.headers['user-id'];
    const { classId, studentId } = req.params;

    if (!teacherId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    // 驗證老師是否擁有此班級
    const [classResult] = await db.query(
      'SELECT teacher_id FROM classes WHERE id = ?',
      [classId]
    );

    if (classResult.length === 0 || classResult[0].teacher_id !== parseInt(teacherId)) {
      return res.status(403).json({ error: '無權限修改此班級' });
    }

    await db.query(
      'DELETE FROM class_students WHERE class_id = ? AND student_id = ?',
      [classId, studentId]
    );

    res.json({ message: '學生已移除' });
  } catch (error) {
    console.error('Remove student error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// ===== 科目和單元 API ===== //

// 獲取所有科目
app.get('/api/subjects', async (req, res) => {
  try {
    const [subjects] = await db.query('SELECT id, subject_name, description FROM subjects');
    res.json({ subjects });
  } catch (error) {
    console.error('Get subjects error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 獲取所有單元
app.get('/api/units', async (req, res) => {
  try {
    const [units] = await db.query(
      'SELECT u.id, u.unit_name, u.subject_id, s.subject_name FROM units u JOIN subjects s ON u.subject_id = s.id'
    );
    res.json({ units });
  } catch (error) {
    console.error('Get units error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// ===== 題目匯入 API ===== //

// 匯入題目
app.post('/api/teacher/questions/import', async (req, res) => {
  try {
    const teacherId = req.headers['user-id'];
    const { unit_id, difficulty, questions } = req.body;

    if (!teacherId) {
      return res.status(401).json({ error: '未授權訪問' });
    }

    if (!unit_id || !questions || questions.length === 0) {
      return res.status(400).json({ error: '缺少必要參數' });
    }

    // 驗證單元是否存在
    const [unitResult] = await db.query(
      'SELECT id FROM units WHERE id = ?',
      [unit_id]
    );

    if (unitResult.length === 0) {
      return res.status(404).json({ error: '單元不存在' });
    }

    let importedCount = 0;

    // 批量插入題目
    for (const question of questions) {
      if (question.question_text && question.answer_text) {
        const [result] = await db.query(
          `INSERT INTO questions 
           (unit_id, question_text, answer_text, solution_text, difficulty) 
           VALUES (?, ?, ?, ?, ?)`,
          [
            unit_id,
            question.question_text,
            question.answer_text,
            question.solution_text || null,
            question.difficulty || difficulty || 'medium'
          ]
        );

        if (result.insertId) {
          importedCount++;
        }
      }
    }

    res.json({
      message: `成功匯入 ${importedCount} 條題目`,
      imported_count: importedCount
    });
  } catch (error) {
    console.error('Import questions error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// ===== 學生功能 API ===== //

// 1. 獲取題目（帶篩選）
app.get('/api/questions', async (req, res) => {
  try {
    const { unit_id, difficulty, subject_id } = req.query;
    
    let query = 'SELECT q.* FROM questions q JOIN units u ON q.unit_id = u.id WHERE 1=1';
    let params = [];
    
    if (unit_id) {
      query += ' AND q.unit_id = ?';
      params.push(unit_id);
    }
    
    if (difficulty) {
      query += ' AND q.difficulty = ?';
      params.push(difficulty);
    }
    
    if (subject_id) {
      query += ' AND u.subject_id = ?';
      params.push(subject_id);
    }
    
    query += ' ORDER BY q.created_at DESC LIMIT 100';
    
    const [questions] = await db.query(query, params);
    res.json({ questions });
  } catch (error) {
    console.error('Get questions error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 2. 獲取相似題目
app.get('/api/questions/:id/similar', async (req, res) => {
  try {
    const { id } = req.params;
    
    // 先獲取原始題目的信息
    const [originalQuestion] = await db.query(
      'SELECT unit_id, subject_id, difficulty FROM questions WHERE id = ?',
      [id]
    );
    
    if (originalQuestion.length === 0) {
      return res.status(404).json({ error: '題目不存在' });
    }
    
    const { unit_id, difficulty } = originalQuestion[0];
    
    // 獲取相同單元和難度的其他題目作為相似題
    const [similarQuestions] = await db.query(
      `SELECT * FROM questions 
       WHERE unit_id = ? AND difficulty = ? AND id != ? 
       ORDER BY RAND() LIMIT 3`,
      [unit_id, difficulty, id]
    );
    
    res.json({ similarQuestions });
  } catch (error) {
    console.error('Get similar questions error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 3. 保存錯題原因
app.post('/api/student/mistake-reasons', async (req, res) => {
  try {
    const userId = req.headers['user-id'];
    const { question_id, session_id, reason_type, reason_description } = req.body;
    
    if (!userId || !question_id || !reason_type) {
      return res.status(400).json({ error: '缺少必要參數' });
    }
    
    const [result] = await db.query(
      `INSERT INTO mistake_reasons 
       (student_id, question_id, session_id, reason_type, reason_description, recorded_at) 
       VALUES (?, ?, ?, ?, ?, NOW())`,
      [userId, question_id, session_id || null, reason_type, reason_description || null]
    );
    
    res.json({ 
      success: true, 
      id: result.insertId,
      message: '錯題原因已保存' 
    });
  } catch (error) {
    console.error('Save mistake reason error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 4. 獲取學生的錯題原因
app.get('/api/student/mistake-reasons/:questionId', async (req, res) => {
  try {
    const userId = req.headers['user-id'];
    const { questionId } = req.params;
    
    if (!userId) {
      return res.status(401).json({ error: '未授權訪問' });
    }
    
    const [reasons] = await db.query(
      `SELECT * FROM mistake_reasons 
       WHERE student_id = ? AND question_id = ? 
       ORDER BY recorded_at DESC`,
      [userId, questionId]
    );
    
    res.json({ reasons });
  } catch (error) {
    console.error('Get mistake reasons error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 5. 保存教學會話
app.post('/api/teaching-sessions', async (req, res) => {
  try {
    const userId = req.headers['user-id'];
    const { 
      question_id, 
      session_type,
      transcript, 
      whiteboard_data, 
      duration_seconds,
      audio_url
    } = req.body;
    
    if (!userId || !question_id) {
      return res.status(400).json({ error: '缺少必要參數' });
    }
    
    const [result] = await db.query(
      `INSERT INTO teaching_sessions 
       (student_id, question_id, session_type, transcript, whiteboard_data, duration_seconds, audio_url, started_at, created_at) 
       VALUES (?, ?, ?, ?, ?, ?, ?, NOW(), NOW())`,
      [
        userId, 
        question_id, 
        session_type || 'teaching',
        transcript || null,
        whiteboard_data ? JSON.stringify(whiteboard_data) : null,
        duration_seconds || 0,
        audio_url || null
      ]
    );
    
    res.json({ 
      success: true, 
      sessionId: result.insertId,
      message: '教學會話已保存' 
    });
  } catch (error) {
    console.error('Save teaching session error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 6. 獲取教學會話
app.get('/api/teaching-sessions/:id', async (req, res) => {
  try {
    const userId = req.headers['user-id'];
    const { id } = req.params;
    
    if (!userId) {
      return res.status(401).json({ error: '未授權訪問' });
    }
    
    const [sessions] = await db.query(
      `SELECT * FROM teaching_sessions 
       WHERE id = ? AND student_id = ?`,
      [id, userId]
    );
    
    if (sessions.length === 0) {
      return res.status(404).json({ error: '會話不存在' });
    }
    
    const session = sessions[0];
    if (session.whiteboard_data) {
      session.whiteboard_data = JSON.parse(session.whiteboard_data);
    }
    
    res.json({ session });
  } catch (error) {
    console.error('Get teaching session error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 7. 獲取學生所有錯題
app.get('/api/student/mistakes', async (req, res) => {
  try {
    const userId = req.headers['user-id'];
    
    if (!userId) {
      return res.status(401).json({ error: '未授權訪問' });
    }
    
    const [mistakes] = await db.query(
      `SELECT DISTINCT
        q.id,
        q.question_text,
        q.answer_text,
        q.solution_text,
        q.difficulty,
        u.unit_name,
        s.subject_name,
        mr.reason_type,
        mr.reason_description,
        MAX(mr.recorded_at) as last_recorded_at
      FROM mistake_reasons mr
      JOIN questions q ON mr.question_id = q.id
      JOIN units u ON q.unit_id = u.id
      JOIN subjects s ON u.subject_id = s.id
      WHERE mr.student_id = ?
      GROUP BY mr.question_id
      ORDER BY last_recorded_at DESC`,
      [userId]
    );
    
    res.json({ mistakes });
  } catch (error) {
    console.error('Get student mistakes error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// 8. 獲取題目統計
app.get('/api/student/stats', async (req, res) => {
  try {
    const userId = req.headers['user-id'];
    
    if (!userId) {
      return res.status(401).json({ error: '未授權訪問' });
    }
    
    // 總錯題數
    const [mistakeCount] = await db.query(
      'SELECT COUNT(DISTINCT question_id) as total FROM mistake_reasons WHERE student_id = ?',
      [userId]
    );
    
    // 本週新增
    const [weeklyCount] = await db.query(
      `SELECT COUNT(DISTINCT question_id) as total FROM mistake_reasons 
       WHERE student_id = ? AND recorded_at > DATE_SUB(NOW(), INTERVAL 7 DAY)`,
      [userId]
    );
    
    // 錯題原因分佈
    const [reasonDistribution] = await db.query(
      `SELECT reason_type, COUNT(*) as count FROM mistake_reasons 
       WHERE student_id = ? GROUP BY reason_type`,
      [userId]
    );
    
    res.json({
      totalMistakes: mistakeCount[0]?.total || 0,
      weeklyMistakes: weeklyCount[0]?.total || 0,
      reasonDistribution: reasonDistribution || []
    });
  } catch (error) {
    console.error('Get student stats error:', error);
    res.status(500).json({ error: '伺服器錯誤' });
  }
});

// ===== 啟動伺服器 ===== //
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

// 關閉資料庫連接
process.on('SIGINT', () => {
  db.end((err) => {
    if (err) {
      console.error('Error closing database connection:', err.message);
    } else {
      console.log('Database connection closed.');
    }
    process.exit(0);
  });
});