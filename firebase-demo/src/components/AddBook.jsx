// 添加图书组件
import React, { useState } from 'react';
import { addBook } from '../firebase/firestore';
import './AddBook.css';

const AddBook = ({ user, onBookAdded }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // 处理表单输入变化
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 清除错误和成功信息
    if (error) setError('');
    if (success) setSuccess('');
  };

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // 验证表单
    if (!formData.title.trim()) {
      setError('请输入图书标题');
      setLoading(false);
      return;
    }

    if (!formData.description.trim()) {
      setError('请输入图书简介');
      setLoading(false);
      return;
    }

    try {
      const bookData = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        userId: user.uid,
        userEmail: user.email
      };

      const result = await addBook(bookData);

      if (result.success) {
        setSuccess('图书添加成功！');
        setFormData({ title: '', description: '' });
        // 通知父组件刷新图书列表
        if (onBookAdded) {
          onBookAdded();
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('添加图书失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-book-container">
      <div className="add-book-card">
        <h2>添加新图书</h2>
        
        <form onSubmit={handleSubmit} className="add-book-form">
          <div className="form-group">
            <label htmlFor="title">图书标题 *</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              placeholder="请输入图书标题"
              maxLength="100"
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">图书简介 *</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              required
              placeholder="请输入图书简介"
              rows="4"
              maxLength="500"
            />
            <div className="char-count">
              {formData.description.length}/500
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading}
          >
            {loading ? '添加中...' : '添加图书'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AddBook;

