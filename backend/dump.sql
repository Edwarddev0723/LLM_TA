PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE students (
	id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	grade INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO students VALUES('student-001','小明',8,'2025-12-29 08:01:41.589745');
CREATE TABLE knowledge_nodes (
	id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	subject VARCHAR NOT NULL, 
	unit VARCHAR NOT NULL, 
	difficulty INTEGER NOT NULL, 
	description TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO knowledge_nodes VALUES('algebra-linear-eq','一元一次方程式','數學','代數',1,'包含一個未知數的一次方程式，形如 ax + b = c','2025-12-22 14:45:31.881661');
INSERT INTO knowledge_nodes VALUES('algebra-quadratic-eq','一元二次方程式','數學','代數',2,'包含一個未知數的二次方程式，形如 ax² + bx + c = 0','2025-12-22 14:45:31.881665');
INSERT INTO knowledge_nodes VALUES('algebra-factoring','因式分解','數學','代數',2,'將多項式分解為較簡單因式的乘積','2025-12-22 14:45:31.881666');
INSERT INTO knowledge_nodes VALUES('algebra-quadratic-formula','公式解','數學','代數',2,'使用公式 x = (-b ± √(b²-4ac)) / 2a 求解二次方程式','2025-12-22 14:45:31.881667');
INSERT INTO knowledge_nodes VALUES('geometry-triangle','三角形性質','數學','幾何',1,'三角形的基本性質，包含內角和、邊長關係等','2025-12-22 14:45:31.881668');
INSERT INTO knowledge_nodes VALUES('geometry-pythagorean','畢氏定理','數學','幾何',2,'直角三角形中，斜邊平方等於兩股平方和：a² + b² = c²','2025-12-22 14:45:31.881668');
INSERT INTO knowledge_nodes VALUES('geometry-circle','圓的性質','數學','幾何',2,'圓的基本性質，包含圓周、面積、弦、弧等','2025-12-22 14:45:31.881669');
INSERT INTO knowledge_nodes VALUES('stats-mean','平均數','數學','統計',1,'一組數據的算術平均值','2025-12-22 14:45:31.881669');
INSERT INTO knowledge_nodes VALUES('stats-median','中位數','數學','統計',1,'將數據排序後位於中間位置的數值','2025-12-22 14:45:31.881669');
CREATE TABLE questions (
	id VARCHAR NOT NULL, 
	content TEXT NOT NULL, 
	type VARCHAR NOT NULL, 
	subject VARCHAR NOT NULL, 
	unit VARCHAR NOT NULL, 
	difficulty INTEGER NOT NULL, 
	standard_solution TEXT NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO questions VALUES('q-linear-001','解方程式：3x + 5 = 20','CALCULATION','數學','代數',1,unistr('3x + 5 = 20\u000a3x = 20 - 5\u000a3x = 15\u000ax = 5'),'2025-12-22 14:45:31.886410');
INSERT INTO questions VALUES('q-linear-002','解方程式：2(x - 3) = 10','CALCULATION','數學','代數',1,unistr('2(x - 3) = 10\u000a2x - 6 = 10\u000a2x = 16\u000ax = 8'),'2025-12-22 14:45:31.886413');
INSERT INTO questions VALUES('q-linear-003','小明有一些糖果，給了弟弟 5 顆後，剩下的是原來的 2/3。請問小明原來有幾顆糖果？','CALCULATION','數學','代數',2,unistr('設原來有 x 顆糖果\u000ax - 5 = (2/3)x\u000ax - (2/3)x = 5\u000a(1/3)x = 5\u000ax = 15\u000a答：小明原來有 15 顆糖果'),'2025-12-22 14:45:31.886414');
INSERT INTO questions VALUES('q-quadratic-001','解方程式：x² - 5x + 6 = 0','CALCULATION','數學','代數',2,unistr('x² - 5x + 6 = 0\u000a(x - 2)(x - 3) = 0\u000ax = 2 或 x = 3'),'2025-12-22 14:45:31.886414');
INSERT INTO questions VALUES('q-quadratic-002','解方程式：x² + 4x - 5 = 0','CALCULATION','數學','代數',2,unistr('x² + 4x - 5 = 0\u000a(x + 5)(x - 1) = 0\u000ax = -5 或 x = 1'),'2025-12-22 14:45:31.886415');
INSERT INTO questions VALUES('q-quadratic-003','使用公式解求解：2x² - 3x - 2 = 0','CALCULATION','數學','代數',3,unistr('a=2, b=-3, c=-2\u000ax = (3 ± √(9+16)) / 4\u000ax = (3 ± 5) / 4\u000ax = 2 或 x = -1/2'),'2025-12-22 14:45:31.886415');
INSERT INTO questions VALUES('q-geometry-001','一個直角三角形的兩股分別為 3 公分和 4 公分，求斜邊長度。','CALCULATION','數學','幾何',1,unistr('根據畢氏定理：c² = a² + b²\u000ac² = 3² + 4² = 9 + 16 = 25\u000ac = 5\u000a答：斜邊長度為 5 公分'),'2025-12-22 14:45:31.886416');
INSERT INTO questions VALUES('q-geometry-002','一個圓的半徑為 7 公分，求圓的面積。（π 取 22/7）','CALCULATION','數學','幾何',1,unistr('圓面積 = πr²\u000a= (22/7) × 7²\u000a= (22/7) × 49\u000a= 154\u000a答：圓的面積為 154 平方公分'),'2025-12-22 14:45:31.886416');
INSERT INTO questions VALUES('q-geometry-003','三角形 ABC 中，∠A = 50°，∠B = 70°，求 ∠C。','CALCULATION','數學','幾何',1,unistr('三角形內角和 = 180°\u000a∠C = 180° - ∠A - ∠B\u000a∠C = 180° - 50° - 70°\u000a∠C = 60°'),'2025-12-22 14:45:31.886416');
INSERT INTO questions VALUES('q-stats-001','求以下數據的平均數：12, 15, 18, 21, 24','CALCULATION','數學','統計',1,unistr('平均數 = (12 + 15 + 18 + 21 + 24) / 5\u000a= 90 / 5\u000a= 18'),'2025-12-22 14:45:31.886417');
INSERT INTO questions VALUES('q-stats-002','求以下數據的中位數：7, 3, 9, 5, 11, 2, 8','CALCULATION','數學','統計',1,unistr('先排序：2, 3, 5, 7, 8, 9, 11\u000a共 7 個數，中位數是第 4 個\u000a中位數 = 7'),'2025-12-22 14:45:31.886417');
CREATE TABLE embeddings (
	id VARCHAR NOT NULL, 
	content_id VARCHAR NOT NULL, 
	content_type VARCHAR NOT NULL, 
	embedding BLOB NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
CREATE TABLE knowledge_relations (
	from_id VARCHAR NOT NULL, 
	to_id VARCHAR NOT NULL, 
	relation_type VARCHAR NOT NULL, 
	weight FLOAT, 
	PRIMARY KEY (from_id, to_id, relation_type), 
	FOREIGN KEY(from_id) REFERENCES knowledge_nodes (id), 
	FOREIGN KEY(to_id) REFERENCES knowledge_nodes (id)
);
INSERT INTO knowledge_relations VALUES('algebra-linear-eq','algebra-quadratic-eq','PREREQUISITE',1.0);
INSERT INTO knowledge_relations VALUES('algebra-factoring','algebra-quadratic-eq','RELATED',0.8000000000000000444);
INSERT INTO knowledge_relations VALUES('algebra-quadratic-formula','algebra-quadratic-eq','RELATED',0.9000000000000000222);
INSERT INTO knowledge_relations VALUES('geometry-triangle','geometry-pythagorean','PREREQUISITE',1.0);
CREATE TABLE question_knowledge_nodes (
	question_id VARCHAR NOT NULL, 
	node_id VARCHAR NOT NULL, 
	PRIMARY KEY (question_id, node_id), 
	FOREIGN KEY(question_id) REFERENCES questions (id), 
	FOREIGN KEY(node_id) REFERENCES knowledge_nodes (id)
);
CREATE TABLE misconceptions (
	id VARCHAR NOT NULL, 
	question_id VARCHAR, 
	description TEXT NOT NULL, 
	error_type VARCHAR NOT NULL, 
	correction TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
);
INSERT INTO misconceptions VALUES('misc-001','q-linear-001','移項時忘記變號','CONCEPT','移項時要記得變號，正變負、負變正');
INSERT INTO misconceptions VALUES('misc-002','q-quadratic-001','因式分解時找錯因數','CALCULATION','找兩個數相乘等於常數項，相加等於一次項係數');
INSERT INTO misconceptions VALUES('misc-003','q-geometry-001','畢氏定理公式記錯','CONCEPT','畢氏定理：斜邊² = 股¹² + 股²²，斜邊是最長的邊');
CREATE TABLE hints (
	id VARCHAR NOT NULL, 
	question_id VARCHAR, 
	level INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
);
INSERT INTO hints VALUES('hint-001','q-linear-001',1,'想想看，要怎麼把 x 單獨留在等號一邊？');
INSERT INTO hints VALUES('hint-002','q-linear-001',2,'先把 +5 移到等號右邊，記得要變號');
INSERT INTO hints VALUES('hint-003','q-linear-001',3,'3x = 15，兩邊同除以 3 就能得到 x 的值');
INSERT INTO hints VALUES('hint-004','q-quadratic-001',1,'這題可以用因式分解來解');
INSERT INTO hints VALUES('hint-005','q-quadratic-001',2,'找兩個數，相乘等於 6，相加等於 -5');
INSERT INTO hints VALUES('hint-006','q-quadratic-001',3,'這兩個數是 -2 和 -3，所以 (x-2)(x-3)=0');
INSERT INTO hints VALUES('hint-007','q-geometry-001',1,'這是直角三角形，可以用什麼定理？');
INSERT INTO hints VALUES('hint-008','q-geometry-001',2,'畢氏定理：斜邊² = 兩股平方和');
INSERT INTO hints VALUES('hint-009','q-geometry-001',3,'c² = 3² + 4² = 9 + 16 = 25，所以 c = ?');
CREATE TABLE sessions (
	id VARCHAR NOT NULL, 
	student_id VARCHAR, 
	question_id VARCHAR, 
	start_time DATETIME NOT NULL, 
	end_time DATETIME, 
	final_state VARCHAR, 
	concept_coverage FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
);
INSERT INTO sessions VALUES('session-demo-14-0','student-001','q-geometry-002','2025-12-14 18:01:41.590590','2025-12-14 18:18:41.590590','CONSOLIDATING',0.416238523720289355);
INSERT INTO sessions VALUES('session-demo-13-0','student-001','q-quadratic-001','2025-12-15 20:01:41.590590','2025-12-15 20:13:41.590590','CONSOLIDATING',0.52337304266007878);
INSERT INTO sessions VALUES('session-demo-12-0','student-001','q-geometry-001','2025-12-16 21:01:41.590590','2025-12-16 21:25:41.590590','CONSOLIDATING',0.6251048894897826002);
INSERT INTO sessions VALUES('session-demo-12-1','student-001','q-quadratic-001','2025-12-16 15:01:41.590590','2025-12-16 15:14:41.590590','CONSOLIDATING',0.6246747558738092732);
INSERT INTO sessions VALUES('session-demo-12-2','student-001','q-quadratic-001','2025-12-16 12:01:41.590590','2025-12-16 12:17:41.590590','CONSOLIDATING',0.657299814921872394);
INSERT INTO sessions VALUES('session-demo-11-0','student-001','q-geometry-002','2025-12-17 17:01:41.590590','2025-12-17 17:20:41.590590','CONSOLIDATING',0.737708582435778526);
INSERT INTO sessions VALUES('session-demo-11-1','student-001','q-linear-001','2025-12-17 14:01:41.590590','2025-12-17 14:16:41.590590','CONSOLIDATING',0.6415753745281720377);
INSERT INTO sessions VALUES('session-demo-11-2','student-001','q-geometry-003','2025-12-17 18:01:41.590590','2025-12-17 18:16:41.590590','CONSOLIDATING',0.6272404692618124278);
INSERT INTO sessions VALUES('session-demo-10-0','student-001','q-linear-003','2025-12-18 20:01:41.590590','2025-12-18 20:23:41.590590','CONSOLIDATING',0.5240385708694971223);
INSERT INTO sessions VALUES('session-demo-10-1','student-001','q-geometry-003','2025-12-18 23:01:41.590590','2025-12-18 23:12:41.590590','CONSOLIDATING',0.7513793980990302047);
INSERT INTO sessions VALUES('session-demo-09-0','student-001','q-stats-001','2025-12-19 17:01:41.590590','2025-12-19 17:14:41.590590','CONSOLIDATING',0.6933133497076531259);
INSERT INTO sessions VALUES('session-demo-09-1','student-001','q-geometry-001','2025-12-19 17:01:41.590590','2025-12-19 17:07:41.590590','CONSOLIDATING',0.6449447794580498438);
INSERT INTO sessions VALUES('session-demo-09-2','student-001','q-geometry-001','2025-12-19 19:01:41.590590','2025-12-19 19:20:41.590590','CONSOLIDATING',0.7387672245129541792);
INSERT INTO sessions VALUES('session-demo-08-0','student-001','q-geometry-001','2025-12-20 15:01:41.590590','2025-12-20 15:18:41.590590','CONSOLIDATING',0.6062684886289716468);
INSERT INTO sessions VALUES('session-demo-08-1','student-001','q-geometry-003','2025-12-20 18:01:41.590590','2025-12-20 18:08:41.590590','CONSOLIDATING',0.7154062649266844654);
INSERT INTO sessions VALUES('session-demo-07-0','student-001','q-stats-002','2025-12-21 18:01:41.590590','2025-12-21 18:13:41.590590','CONSOLIDATING',0.7247212016235802246);
INSERT INTO sessions VALUES('session-demo-06-0','student-001','q-quadratic-002','2025-12-22 20:01:41.590590','2025-12-22 20:06:41.590590','CONSOLIDATING',0.7276543186954482766);
INSERT INTO sessions VALUES('session-demo-05-0','student-001','q-quadratic-002','2025-12-23 11:01:41.590590','2025-12-23 11:21:41.590590','CONSOLIDATING',0.896783741971829862);
INSERT INTO sessions VALUES('session-demo-05-1','student-001','q-stats-001','2025-12-23 17:01:41.590590','2025-12-23 17:07:41.590590','CONSOLIDATING',0.7012028764441435858);
INSERT INTO sessions VALUES('session-demo-05-2','student-001','q-geometry-001','2025-12-23 22:01:41.590590','2025-12-23 22:23:41.590590','CONSOLIDATING',0.8140457352262869817);
INSERT INTO sessions VALUES('session-demo-04-0','student-001','q-quadratic-001','2025-12-24 14:01:41.590590','2025-12-24 14:24:41.590590','CONSOLIDATING',0.8458020059174059524);
INSERT INTO sessions VALUES('session-demo-04-1','student-001','q-stats-002','2025-12-24 20:01:41.590590','2025-12-24 20:12:41.590590','CONSOLIDATING',0.9060288168091474859);
INSERT INTO sessions VALUES('session-demo-04-2','student-001','q-geometry-003','2025-12-24 11:01:41.590590','2025-12-24 11:24:41.590590','CONSOLIDATING',0.8507733994265920253);
INSERT INTO sessions VALUES('session-demo-03-0','student-001','q-linear-002','2025-12-25 20:01:41.590590','2025-12-25 20:16:41.590590','CONSOLIDATING',0.8344062190894637743);
INSERT INTO sessions VALUES('session-demo-02-0','student-001','q-linear-003','2025-12-26 16:01:41.590590','2025-12-26 16:07:41.590590','CONSOLIDATING',0.8207036875678795917);
INSERT INTO sessions VALUES('session-demo-02-1','student-001','q-geometry-002','2025-12-26 20:01:41.590590','2025-12-26 20:24:41.590590','CONSOLIDATING',0.9164536287988397367);
INSERT INTO sessions VALUES('session-demo-02-2','student-001','q-geometry-001','2025-12-26 14:01:41.590590','2025-12-26 14:16:41.590590','CONSOLIDATING',0.8656205275391996023);
INSERT INTO sessions VALUES('session-demo-01-0','student-001','q-stats-001','2025-12-27 16:01:41.590590','2025-12-27 16:21:41.590590','CONSOLIDATING',0.949999999999999956);
INSERT INTO sessions VALUES('session-demo-00-0','student-001','q-linear-001','2025-12-28 15:01:41.590590','2025-12-28 15:16:41.590590','CONSOLIDATING',0.949999999999999956);
INSERT INTO sessions VALUES('session-demo-00-1','student-001','q-geometry-001','2025-12-28 11:01:41.590590','2025-12-28 11:10:41.590590','CONSOLIDATING',0.840723952510710526);
CREATE TABLE error_records (
	id VARCHAR NOT NULL, 
	student_id VARCHAR, 
	question_id VARCHAR, 
	student_answer TEXT NOT NULL, 
	correct_answer TEXT NOT NULL, 
	error_type VARCHAR NOT NULL, 
	error_tags TEXT, 
	timestamp DATETIME NOT NULL, 
	repaired BOOLEAN, 
	repaired_at DATETIME, session_id VARCHAR REFERENCES sessions(id), concept VARCHAR, unit VARCHAR, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, is_repaired BOOLEAN DEFAULT 0, recurrence_count INTEGER DEFAULT 0, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES students (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
);
INSERT INTO error_records VALUES('error-session-demo-13-0','student-001','q-quadratic-001','錯誤答案示例','正確答案示例','CONCEPT',NULL,'2025-12-15 20:01:41.590590',1,NULL,'session-demo-13-0','代數','代數','2025-12-15 20:01:41.590590',0,0);
INSERT INTO error_records VALUES('error-session-demo-11-0','student-001','q-geometry-002','錯誤答案示例','正確答案示例','CALCULATION',NULL,'2025-12-17 17:01:41.590590',1,NULL,'session-demo-11-0','幾何','幾何','2025-12-17 17:01:41.590590',0,0);
INSERT INTO error_records VALUES('error-session-demo-10-0','student-001','q-linear-003','錯誤答案示例','正確答案示例','CONCEPT',NULL,'2025-12-18 20:01:41.590590',1,NULL,'session-demo-10-0','代數','代數','2025-12-18 20:01:41.590590',0,0);
INSERT INTO error_records VALUES('error-session-demo-10-1','student-001','q-geometry-003','錯誤答案示例','正確答案示例','CARELESS',NULL,'2025-12-18 23:01:41.590590',1,NULL,'session-demo-10-1','幾何','幾何','2025-12-18 23:01:41.590590',0,0);
INSERT INTO error_records VALUES('error-session-demo-09-1','student-001','q-geometry-001','錯誤答案示例','正確答案示例','CONCEPT',NULL,'2025-12-19 17:01:41.590590',1,NULL,'session-demo-09-1','幾何','幾何','2025-12-19 17:01:41.590590',0,0);
INSERT INTO error_records VALUES('error-session-demo-08-0','student-001','q-geometry-001','錯誤答案示例','正確答案示例','CALCULATION',NULL,'2025-12-20 15:01:41.590590',1,NULL,'session-demo-08-0','幾何','幾何','2025-12-20 15:01:41.590590',1,0);
INSERT INTO error_records VALUES('error-session-demo-08-1','student-001','q-geometry-003','錯誤答案示例','正確答案示例','CARELESS',NULL,'2025-12-20 18:01:41.590590',1,NULL,'session-demo-08-1','幾何','幾何','2025-12-20 18:01:41.590590',0,0);
INSERT INTO error_records VALUES('error-session-demo-06-0','student-001','q-quadratic-002','錯誤答案示例','正確答案示例','CONCEPT',NULL,'2025-12-22 20:01:41.590590',1,NULL,'session-demo-06-0','代數','代數','2025-12-22 20:01:41.590590',1,0);
INSERT INTO error_records VALUES('error-session-demo-05-2','student-001','q-geometry-001','錯誤答案示例','正確答案示例','CARELESS',NULL,'2025-12-23 22:01:41.590590',1,NULL,'session-demo-05-2','幾何','幾何','2025-12-23 22:01:41.590590',0,0);
INSERT INTO error_records VALUES('error-session-demo-04-2','student-001','q-geometry-003','錯誤答案示例','正確答案示例','CALCULATION',NULL,'2025-12-24 11:01:41.590590',0,NULL,'session-demo-04-2','幾何','幾何','2025-12-24 11:01:41.590590',1,0);
INSERT INTO error_records VALUES('error-session-demo-02-0','student-001','q-linear-003','錯誤答案示例','正確答案示例','CALCULATION',NULL,'2025-12-26 16:01:41.590590',0,NULL,'session-demo-02-0','代數','代數','2025-12-26 16:01:41.590590',1,0);
CREATE TABLE conversation_turns (
	id VARCHAR NOT NULL, 
	session_id VARCHAR, 
	turn_number INTEGER NOT NULL, 
	speaker VARCHAR NOT NULL, 
	content TEXT NOT NULL, 
	fsm_state VARCHAR NOT NULL, 
	timestamp DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES sessions (id)
);
CREATE TABLE learning_metrics (
	id VARCHAR NOT NULL, 
	session_id VARCHAR, 
	wpm FLOAT, 
	pause_rate FLOAT, 
	hint_dependency FLOAT, 
	concept_coverage FLOAT, 
	focus_duration FLOAT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES sessions (id)
);
INSERT INTO learning_metrics VALUES('metrics-session-demo-14-0','session-demo-14-0',65.0,0.25,0.5,0.416238523720289355,849.477461524158116,'2025-12-14 18:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-13-0','session-demo-13-0',120.0,0.2399999999999999912,0.4749999999999999778,0.52337304266007878,596.6474422074700214,'2025-12-15 20:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-12-0','session-demo-12-0',89.0,0.2300000000000000099,0.4500000000000000111,0.6251048894897826002,1147.190730135674129,'2025-12-16 21:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-12-1','session-demo-12-1',84.0,0.2300000000000000099,0.4500000000000000111,0.6246747558738092732,657.9291439535446671,'2025-12-16 15:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-12-2','session-demo-12-2',88.0,0.2300000000000000099,0.4500000000000000111,0.657299814921872394,812.4697554499612124,'2025-12-16 12:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-11-0','session-demo-11-0',91.0,0.2200000000000000011,0.4249999999999999889,0.737708582435778526,969.434221570362752,'2025-12-17 17:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-11-1','session-demo-11-1',78.0,0.2200000000000000011,0.4249999999999999889,0.6415753745281720377,710.2005583137498662,'2025-12-17 14:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-11-2','session-demo-11-2',102.0,0.2200000000000000011,0.4249999999999999889,0.6272404692618124278,730.0749209976054317,'2025-12-17 18:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-10-0','session-demo-10-0',116.0,0.2099999999999999923,0.4000000000000000222,0.5240385708694971223,1229.67596855524539,'2025-12-18 20:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-10-1','session-demo-10-1',91.0,0.2099999999999999923,0.4000000000000000222,0.7513793980990302047,492.3239744417019779,'2025-12-18 23:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-09-0','session-demo-09-0',74.0,0.2000000000000000111,0.375,0.6933133497076531259,648.4228260298837085,'2025-12-19 17:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-09-1','session-demo-09-1',113.0,0.2000000000000000111,0.375,0.6449447794580498438,270.8414324477623723,'2025-12-19 17:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-09-2','session-demo-09-2',71.0,0.2000000000000000111,0.375,0.7387672245129541792,1023.214520601195545,'2025-12-19 19:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-08-0','session-demo-08-0',95.0,0.1900000000000000022,0.3499999999999999778,0.6062684886289716468,779.9907477973358709,'2025-12-20 15:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-08-1','session-demo-08-1',111.0,0.1900000000000000022,0.3499999999999999778,0.7154062649266844654,301.0814480339394663,'2025-12-20 18:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-07-0','session-demo-07-0',80.0,0.1799999999999999934,0.3249999999999999555,0.7247212016235802246,522.2764708666535398,'2025-12-21 18:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-06-0','session-demo-06-0',128.0,0.1699999999999999844,0.2999999999999999889,0.7276543186954482766,239.6845227310176086,'2025-12-22 20:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-05-0','session-demo-05-0',126.0,0.1600000000000000033,0.2750000000000000222,0.896783741971829862,871.0475385630884376,'2025-12-23 11:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-05-1','session-demo-05-1',80.0,0.1600000000000000033,0.2750000000000000222,0.7012028764441435858,325.5966955549318414,'2025-12-23 17:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-05-2','session-demo-05-2',127.0,0.1600000000000000033,0.2750000000000000222,0.8140457352262869817,936.621132295979465,'2025-12-23 22:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-04-0','session-demo-04-0',95.0,0.1499999999999999945,0.25,0.8458020059174059524,1168.647577288591038,'2025-12-24 14:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-04-1','session-demo-04-1',84.0,0.1499999999999999945,0.25,0.9060288168091474859,586.5324043807138424,'2025-12-24 20:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-04-2','session-demo-04-2',113.0,0.1499999999999999945,0.25,0.8507733994265920253,1249.290237064883285,'2025-12-24 11:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-03-0','session-demo-03-0',115.0,0.1400000000000000134,0.2249999999999999777,0.8344062190894637743,818.9394475082226564,'2025-12-25 20:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-02-0','session-demo-02-0',138.0,0.1300000000000000044,0.1999999999999999555,0.8207036875678795917,284.2072248401748312,'2025-12-26 16:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-02-1','session-demo-02-1',128.0,0.1300000000000000044,0.1999999999999999555,0.9164536287988397367,1051.862171668645942,'2025-12-26 20:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-02-2','session-demo-02-2',143.0,0.1300000000000000044,0.1999999999999999555,0.8656205275391996023,716.3786696639341472,'2025-12-26 14:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-01-0','session-demo-01-0',122.0,0.1199999999999999956,0.1749999999999999889,0.949999999999999956,1076.21418832518566,'2025-12-27 16:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-00-0','session-demo-00-0',120.0,0.1099999999999999867,0.1499999999999999667,0.949999999999999956,845.9236690360360171,'2025-12-28 15:01:41.590590');
INSERT INTO learning_metrics VALUES('metrics-session-demo-00-1','session-demo-00-1',88.0,0.1099999999999999867,0.1499999999999999667,0.840723952510710526,414.3353502578779626,'2025-12-28 11:01:41.590590');
CREATE TABLE pauses (
	id VARCHAR NOT NULL, 
	session_id VARCHAR, 
	start_time FLOAT NOT NULL, 
	end_time FLOAT NOT NULL, 
	duration FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES sessions (id)
);
CREATE TABLE hint_usages (
	id VARCHAR NOT NULL, 
	session_id VARCHAR, 
	hint_level INTEGER NOT NULL, 
	concept VARCHAR, 
	timestamp DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES sessions (id)
);
INSERT INTO hint_usages VALUES('f94f192f-9883-4d49-8988-0809a955aa70','0b962624-aa86-46de-bbf3-859481fd11c6',1,'linear-equation','2025-12-26 12:11:39.017490');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-13-0-0','session-demo-13-0',1,'代數','2025-12-15 20:07:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-12-2-0','session-demo-12-2',1,'代數','2025-12-16 12:10:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-12-2-1','session-demo-12-2',2,'代數','2025-12-16 12:10:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-12-2-2','session-demo-12-2',3,'代數','2025-12-16 12:05:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-11-1-0','session-demo-11-1',1,'代數','2025-12-17 14:04:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-11-2-0','session-demo-11-2',1,'幾何','2025-12-17 18:06:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-11-2-1','session-demo-11-2',2,'幾何','2025-12-17 18:04:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-09-0-0','session-demo-09-0',1,'統計','2025-12-19 17:03:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-09-0-1','session-demo-09-0',2,'統計','2025-12-19 17:14:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-09-0-2','session-demo-09-0',3,'統計','2025-12-19 17:07:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-09-1-0','session-demo-09-1',1,'幾何','2025-12-19 17:03:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-09-1-1','session-demo-09-1',2,'幾何','2025-12-19 17:03:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-09-2-0','session-demo-09-2',1,'幾何','2025-12-19 19:13:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-08-0-0','session-demo-08-0',1,'幾何','2025-12-20 15:18:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-08-1-0','session-demo-08-1',1,'幾何','2025-12-20 18:06:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-07-0-0','session-demo-07-0',1,'統計','2025-12-21 18:05:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-07-0-1','session-demo-07-0',2,'統計','2025-12-21 18:07:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-07-0-2','session-demo-07-0',3,'統計','2025-12-21 18:03:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-06-0-0','session-demo-06-0',1,'代數','2025-12-22 20:02:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-05-0-0','session-demo-05-0',1,'代數','2025-12-23 11:16:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-05-0-1','session-demo-05-0',2,'代數','2025-12-23 11:07:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-05-1-0','session-demo-05-1',1,'統計','2025-12-23 17:06:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-05-1-1','session-demo-05-1',2,'統計','2025-12-23 17:05:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-05-1-2','session-demo-05-1',3,'統計','2025-12-23 17:02:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-05-2-0','session-demo-05-2',1,'幾何','2025-12-23 22:04:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-04-2-0','session-demo-04-2',1,'幾何','2025-12-24 11:06:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-03-0-0','session-demo-03-0',1,'代數','2025-12-25 20:10:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-03-0-1','session-demo-03-0',2,'代數','2025-12-25 20:05:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-02-2-0','session-demo-02-2',1,'幾何','2025-12-26 14:14:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-00-0-0','session-demo-00-0',1,'代數','2025-12-28 15:11:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-00-1-0','session-demo-00-1',1,'幾何','2025-12-28 11:02:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-00-1-1','session-demo-00-1',2,'幾何','2025-12-28 11:10:41.590590');
INSERT INTO hint_usages VALUES('hint-usage-session-demo-00-1-2','session-demo-00-1',3,'幾何','2025-12-28 11:04:41.590590');
CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(7) NOT NULL, 
	full_name VARCHAR(255) NOT NULL, 
	grade VARCHAR(50), 
	class_name VARCHAR(100), 
	phone VARCHAR(20), 
	student_name VARCHAR(255), 
	relationship_type VARCHAR(50), 
	id_document_path VARCHAR(500), 
	verification_status VARCHAR(8), 
	verified_by INTEGER, 
	verified_at DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(verified_by) REFERENCES users (id)
);
INSERT INTO users VALUES(1,'test@example.com','5954fe175c458e109b5d5d4f72639770955c287a31e4e5e2d8f9ab85b1e0e606','STUDENT','Test Student',NULL,NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-25 05:01:54.158410','2025-12-25 05:01:54.158415');
INSERT INTO users VALUES(2,'1234test@test.com','c54aac2794090dcefa998bf9320994818e34294122f7d69bed97dfde47ad1c6c','STUDENT','黃仁和',NULL,NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-25 14:12:15.506355','2025-12-25 14:12:15.506366');
INSERT INTO users VALUES(3,'admin@test.com','2d67e6e967452cb3a21ee5a2605963ab4bef4cd052de9e7c1463284feadc215e','ADMIN','系統管理員',NULL,NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-26 12:17:58.664929','2025-12-26 12:17:58.664933');
INSERT INTO users VALUES(4,'teacher@test.com','43fc8430e8ea9564752e93bf36a476b401b5c1ce73236d8c52ddbb21bbd0c474','TEACHER','王老師',NULL,NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-26 12:17:58.664934','2025-12-26 12:17:58.664934');
INSERT INTO users VALUES(5,'teacher2@test.com','43fc8430e8ea9564752e93bf36a476b401b5c1ce73236d8c52ddbb21bbd0c474','TEACHER','李老師',NULL,NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-26 12:17:58.664935','2025-12-26 12:17:58.664935');
INSERT INTO users VALUES(6,'student@test.com','6361fe69f5d56d3c3a70d31844cdf2dfeb2b7b1aee48da4b416c548f59460517','STUDENT','小明','國中二年級',NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-26 12:17:58.664936','2025-12-26 12:17:58.664936');
INSERT INTO users VALUES(7,'student2@test.com','6361fe69f5d56d3c3a70d31844cdf2dfeb2b7b1aee48da4b416c548f59460517','STUDENT','小華','國中一年級',NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-26 12:17:58.664937','2025-12-26 12:17:58.664937');
INSERT INTO users VALUES(8,'student3@test.com','6361fe69f5d56d3c3a70d31844cdf2dfeb2b7b1aee48da4b416c548f59460517','STUDENT','小美','國中三年級',NULL,NULL,NULL,NULL,NULL,'APPROVED',NULL,NULL,'2025-12-26 12:17:58.664937','2025-12-26 12:17:58.664938');
INSERT INTO users VALUES(9,'parent@test.com','034dba96e3ee4b34ea26f30c0c50bea00efd9e0212a42691efdb78dda160fd25','PARENT','陳爸爸',NULL,NULL,NULL,'小明',NULL,NULL,'APPROVED',NULL,NULL,'2025-12-26 12:17:58.664938','2025-12-26 12:17:58.664938');
CREATE TABLE subjects (
	id INTEGER NOT NULL, 
	subject_name VARCHAR(100) NOT NULL, 
	description TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (subject_name)
);
CREATE TABLE classes (
	id INTEGER NOT NULL, 
	class_name VARCHAR(255) NOT NULL, 
	description TEXT, 
	teacher_id INTEGER NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(teacher_id) REFERENCES users (id)
);
CREATE TABLE parent_students (
	id INTEGER NOT NULL, 
	parent_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	relationship_type VARCHAR(50), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE units (
	id INTEGER NOT NULL, 
	subject_id INTEGER NOT NULL, 
	unit_name VARCHAR(255) NOT NULL, 
	description TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subject_id) REFERENCES subjects (id) ON DELETE CASCADE
);
CREATE TABLE class_students (
	id INTEGER NOT NULL, 
	class_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	joined_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE questions_v2 (
	id INTEGER NOT NULL, 
	unit_id INTEGER NOT NULL, 
	question_text TEXT NOT NULL, 
	question_image VARCHAR(255), 
	difficulty VARCHAR(6), 
	answer_text TEXT, 
	solution_text TEXT, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(unit_id) REFERENCES units (id) ON DELETE CASCADE
);
CREATE TABLE mistake_reasons (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	question_id INTEGER NOT NULL, 
	session_id INTEGER, 
	reason_type VARCHAR(50), 
	reason_description TEXT, 
	recorded_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(question_id) REFERENCES questions_v2 (id) ON DELETE CASCADE
);
CREATE TABLE teaching_sessions (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	question_id INTEGER, 
	session_type VARCHAR(20), 
	whiteboard_data TEXT, 
	transcript TEXT, 
	audio_url VARCHAR(255), 
	duration_seconds INTEGER, 
	started_at DATETIME, 
	ended_at DATETIME, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(question_id) REFERENCES questions_v2 (id) ON DELETE SET NULL
);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_classes_teacher_id ON classes (teacher_id);
CREATE INDEX ix_parent_students_parent_id ON parent_students (parent_id);
CREATE INDEX ix_parent_students_student_id ON parent_students (student_id);
CREATE INDEX ix_units_subject_id ON units (subject_id);
CREATE INDEX ix_class_students_class_id ON class_students (class_id);
CREATE INDEX ix_class_students_student_id ON class_students (student_id);
CREATE INDEX ix_questions_v2_difficulty ON questions_v2 (difficulty);
CREATE INDEX ix_questions_v2_unit_id ON questions_v2 (unit_id);
CREATE INDEX ix_mistake_reasons_student_id ON mistake_reasons (student_id);
CREATE INDEX ix_mistake_reasons_question_id ON mistake_reasons (question_id);
CREATE INDEX ix_teaching_sessions_student_id ON teaching_sessions (student_id);
COMMIT;
