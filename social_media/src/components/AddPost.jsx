// 添加消息组件
import React, { useState } from 'react';
import { addPost } from '../firebase/firestore';
import './AddPost.css';

const AddPost = ({ user, onPostAdded }) => {
  const [formData, setFormData] = useState({
    title: '',
    content: ''
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
      setError('请输入消息标题');
      setLoading(false);
      return;
    }

    if (!formData.content.trim()) {
      setError('请输入消息内容');
      setLoading(false);
      return;
    }

    try {
      const postData = {
        title: formData.title.trim(),
        content: formData.content.trim(),
        userId: user.uid,
        userEmail: user.email
      };

      const result = await addPost(postData);

      if (result.success) {
        setSuccess('消息发布成功！');
        setFormData({ title: '', content: '' });
        // 通知父组件刷新消息列表
        if (onPostAdded) {
          onPostAdded();
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('发布消息失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-post-container">
      <div className="add-post-card">
        <h2>发布新消息</h2>
        
        <form onSubmit={handleSubmit} className="add-post-form">
          <div className="form-group">
            <label htmlFor="title">标题 *</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              placeholder="请输入标题"
              maxLength="100"
            />
          </div>

          <div className="form-group">
            <label htmlFor="content">内容 *</label>
            <textarea
              id="content"
              name="content"
              value={formData.content}
              onChange={handleInputChange}
              required
              placeholder="分享你的想法..."
              rows="4"
              maxLength="500"
            />
            <div className="char-count">
              {formData.content.length}/500
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading}
          >
            {loading ? '发布中...' : '发布'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AddPost;

