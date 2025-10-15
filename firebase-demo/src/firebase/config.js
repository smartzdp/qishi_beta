// Firebase配置文件
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Firebase配置对象
// 注意：请将以下配置替换为您自己的Firebase项目配置
const firebaseConfig = {
  apiKey: "AIzaSyAl5966GNZpEpWkgCpHvCktuMXV5sAKyFc",
  authDomain: "mybase-c804e.firebaseapp.com",
  projectId: "mybase-c804e",
  storageBucket: "mybase-c804e.firebasestorage.app",
  messagingSenderId: "226810225204",
  appId: "1:226810225204:web:d503f33981f87e3458a061"
};

// 添加错误处理
console.log('Firebase配置:', firebaseConfig);

// 初始化Firebase应用
let app;
try {
  app = initializeApp(firebaseConfig);
  console.log('Firebase应用初始化成功');
} catch (error) {
  console.error('Firebase应用初始化失败:', error);
  throw error;
}

// 初始化Firebase认证
let auth;
try {
  auth = getAuth(app);
  console.log('Firebase认证初始化成功');
} catch (error) {
  console.error('Firebase认证初始化失败:', error);
  throw error;
}

// 初始化Firestore数据库
let db;
try {
  db = getFirestore(app);
  console.log('Firestore数据库初始化成功');
} catch (error) {
  console.error('Firestore数据库初始化失败:', error);
  throw error;
}

export { auth, db };

export default app;
