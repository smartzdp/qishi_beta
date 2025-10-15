// Firebase配置文件
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Firebase配置对象
// 注意：请将以下配置替换为您自己的Firebase项目配置
const firebaseConfig = {
  apiKey: "AIzaSyCIGnOqcK2ndg7P9IwrEqNq23TmyjhJWxI",
  authDomain: "social-media-7679b.firebaseapp.com",
  projectId: "social-media-7679b",
  storageBucket: "social-media-7679b.firebasestorage.app",
  messagingSenderId: "167317687189",
  appId: "1:167317687189:web:57dc8fc4ff66eee298849c"
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
