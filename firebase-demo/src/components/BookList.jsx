// 图书列表组件
import React, { useState, useEffect } from 'react';
import { getAllBooks, updateBook, deleteBook } from '../firebase/firestore';
import './BookList.css';

const BookList = ({ user }) => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ title: '', description: '' });

  // 加载图书列表
  const loadBooks = async () => {
    try {
      setLoading(true);
      const result = await getAllBooks();
      if (result.success) {
        setBooks(result.books);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('加载图书列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载图书
  useEffect(() => {
    loadBooks();
  }, []);

  // 开始编辑
  const startEdit = (book) => {
    setEditingId(book.id);
    setEditForm({ title: book.title || '', description: book.description || '' });
  };

  // 取消编辑
  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({ title: '', description: '' });
  };

  // 提交保存
  const saveEdit = async (bookId) => {
    if (!editForm.title.trim()) return alert('标题不能为空');
    if (!editForm.description.trim()) return alert('简介不能为空');
    const res = await updateBook(bookId, {
      title: editForm.title.trim(),
      description: editForm.description.trim()
    });
    if (res.success) {
      await loadBooks();
      cancelEdit();
    } else {
      alert('保存失败：' + res.error);
    }
  };

  // 删除图书
  const removeBook = async (bookId) => {
    if (!confirm('确定要删除这本图书吗？此操作不可恢复。')) return;
    const res = await deleteBook(bookId);
    if (res.success) {
      await loadBooks();
    } else {
      alert('删除失败：' + res.error);
    }
  };

  // 格式化时间
  const formatDate = (timestamp) => {
    if (!timestamp) return '未知时间';
    const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
    return date.toLocaleString('zh-CN');
  };

  if (loading) {
    return (
      <div className="book-list-container">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="book-list-container">
        <div className="error-message">
          <p>加载失败：{error}</p>
          <button onClick={loadBooks} className="retry-btn">重试</button>
        </div>
      </div>
    );
  }

  return (
    <div className="book-list-container">
      <div className="book-list-header">
        <h2>图书列表</h2>
        <p className="book-count">共 {books.length} 本图书</p>
      </div>

      {books.length === 0 ? (
        <div className="empty-state">
          <p>暂无图书，{user ? '添加第一本图书吧！' : '登录后可以添加图书'}</p>
        </div>
      ) : (
        <div className="books-grid">
          {books.map((book) => (
            <div key={book.id} className="book-card">
              <div className="book-header">
                {editingId === book.id ? (
                  <input
                    className="book-title-input"
                    value={editForm.title}
                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    maxLength="100"
                  />
                ) : (
                  <h3 className="book-title">{book.title}</h3>
                )}
                <span className="book-author">by {book.userEmail}</span>
              </div>

              <div className="book-content">
                {editingId === book.id ? (
                  <textarea
                    className="book-desc-input"
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows="4"
                    maxLength="500"
                  />
                ) : (
                  <p className="book-description">{book.description}</p>
                )}
              </div>
              
              <div className="book-footer">
                <span className="book-date">
                  添加时间：{formatDate(book.createdAt)}
                </span>
                {user && user.uid === book.userId && (
                  editingId === book.id ? (
                    <div className="edit-actions">
                      <button className="action-btn primary" onClick={() => saveEdit(book.id)}>保存</button>
                      <button className="action-btn" onClick={cancelEdit}>取消</button>
                    </div>
                  ) : (
                    <div className="edit-actions">
                      <span className="book-owner">我的图书</span>
                      <div className="edit-actions-buttons">
                        <button className="action-btn" onClick={() => startEdit(book)}>编辑</button>
                        <button className="action-btn danger" onClick={() => removeBook(book.id)}>删除</button>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BookList;
