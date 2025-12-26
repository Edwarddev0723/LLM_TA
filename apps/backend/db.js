require('dotenv').config();
const mysql = require('mysql2');

// 建立 MySQL 連接池
const dbConfig = {
  host: 'localhost',
  user: 'root',
  password: '',
  database: 'ai_ta_db',
  port: 3306,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
};

console.log(`Attempting to connect to MySQL at ${dbConfig.host}:${dbConfig.port} as ${dbConfig.user}...`);

const db = mysql.createPool(dbConfig);

db.getConnection((err, connection) => {
  if (err) {
    console.error('Error connecting to MySQL database:');
    console.error('Code:', err.code);
    console.error('Message:', err.message);
    console.error('Errno:', err.errno);
    return;
  }
  console.log('Connected to the MySQL database successfully!');
  connection.release();
});

// 導出連接池（同時支援回調和 promise）
module.exports = db;
