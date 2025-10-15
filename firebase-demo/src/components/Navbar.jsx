// 导航栏组件
import React from 'react';
import { logoutUser } from '../firebase/auth';
import './Navbar.css';

const Navbar = ({ user, onLogout }) => {
  // 处理登出
  const handleLogout = async () => {
    try {
      const result = await logoutUser();
      if (result.success) {
        onLogout();
      } else {
        alert('登出失败：' + result.error);
      }
    } catch (error) {
      alert('登出失败：' + error.message);
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <h1>📚 图书管理系统</h1>
        </div>
        
        <div className="navbar-menu">
          {user ? (
            <div className="user-menu">
              <span className="user-info">
                欢迎，{user.email}
              </span>
              <button 
                onClick={handleLogout}
                className="logout-btn"
              >
                登出
              </button>
            </div>
          ) : (
            <div className="guest-info">
              <span>游客模式 - 只能查看图书</span>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

