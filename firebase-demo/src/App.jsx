// 主应用组件
import React, { useState, useEffect } from 'react';
import { onAuthStateChange, handleGoogleRedirect } from './firebase/auth';
import { testFirestoreConnection } from './firebase/firestore';
import Navbar from './components/Navbar';
import Login from './components/Login';
import BookList from './components/BookList';
import AddBook from './components/AddBook';
import './App.css';

const App = () => {
  const [user, setUser] = useState(null); // 当前用户状态
  const [loading, setLoading] = useState(true); // 加载状态
  const [refreshBooks, setRefreshBooks] = useState(0); // 用于触发图书列表刷新

  // 监听用户认证状态变化
  useEffect(() => {
    const unsubscribe = onAuthStateChange((user) => {
      setUser(user);
      setLoading(false);
    });

    // 处理Google重定向结果
    handleGoogleRedirect().then((result) => {
      if (result && result.success && result.user) {
        setUser(result.user);
      }
    }).catch(() => {});

    // 测试Firestore连接
    testFirestoreConnection().then(result => {
      if (result.success) {
        console.log('✅ Firestore连接正常');
      } else {
        console.error('❌ Firestore连接失败:', result.error);
      }
    });

    // 清理监听器
    return () => unsubscribe();
  }, []);

  // 处理登录成功
  const handleLoginSuccess = (user) => {
    setUser(user);
  };

  // 处理登出
  const handleLogout = () => {
    setUser(null);
  };

  // 处理图书添加成功
  const handleBookAdded = () => {
    setRefreshBooks(prev => prev + 1);
  };

  // 显示加载状态
  if (loading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* 导航栏 */}
      <Navbar user={user} onLogout={handleLogout} />
      
      <div className="app-content">
        {user ? (
          // 已登录用户界面
          <div className="logged-in-content">
            <div className="content-section">
              <AddBook user={user} onBookAdded={handleBookAdded} />
            </div>
            <div className="content-section">
              <BookList key={refreshBooks} user={user} />
            </div>
          </div>
        ) : (
          // 未登录用户界面
          <div className="guest-content">
            <div className="login-section">
              <Login onLoginSuccess={handleLoginSuccess} />
            </div>
            <div className="books-section">
              <BookList key={refreshBooks} user={user} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
