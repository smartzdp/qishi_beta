// 消息列表组件
import React, { useState, useEffect } from 'react';
import { getAllPosts, updatePost, deletePost, toggleLike, addComment, deleteComment } from '../firebase/firestore';
import './PostList.css';

const PostList = ({ user }) => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ title: '', content: '' });
  const [sortBy, setSortBy] = useState('time'); // 'time' 或 'likes' 或 'comments'
  const [commentingId, setCommentingId] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [expandedComments, setExpandedComments] = useState({});

  // 加载消息列表
  const loadPosts = async () => {
    try {
      setLoading(true);
      const result = await getAllPosts();
      if (result.success) {
        setPosts(result.posts);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('加载消息列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载消息
  useEffect(() => {
    loadPosts();
  }, []);

  // 排序消息
  const sortedPosts = [...posts].sort((a, b) => {
    if (sortBy === 'likes') {
      return (b.likesCount || 0) - (a.likesCount || 0);
    } else if (sortBy === 'comments') {
      return (b.comments?.length || 0) - (a.comments?.length || 0);
    } else {
      // 按时间排序
      const aTime = a.createdAt?.toDate?.() || new Date(0);
      const bTime = b.createdAt?.toDate?.() || new Date(0);
      return bTime - aTime;
    }
  });

  // 开始编辑
  const startEdit = (post) => {
    setEditingId(post.id);
    setEditForm({ title: post.title || '', content: post.content || '' });
  };

  // 取消编辑
  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({ title: '', content: '' });
  };

  // 提交保存
  const saveEdit = async (postId) => {
    if (!editForm.title.trim()) return alert('标题不能为空');
    if (!editForm.content.trim()) return alert('内容不能为空');
    const res = await updatePost(postId, {
      title: editForm.title.trim(),
      content: editForm.content.trim()
    });
    if (res.success) {
      await loadPosts();
      cancelEdit();
    } else {
      alert('保存失败：' + res.error);
    }
  };

  // 删除消息
  const removePost = async (postId) => {
    if (!confirm('确定要删除这条消息吗？此操作不可恢复。')) return;
    const res = await deletePost(postId);
    if (res.success) {
      await loadPosts();
    } else {
      alert('删除失败：' + res.error);
    }
  };

  // 点赞/取消点赞
  const handleLike = async (post) => {
    if (!user) {
      alert('请先登录才能点赞');
      return;
    }
    const isLiked = post.likes?.includes(user.uid);
    const res = await toggleLike(post.id, user.uid, isLiked);
    if (res.success) {
      await loadPosts();
    } else {
      alert('点赞失败：' + res.error);
    }
  };

  // 开始回帖
  const startComment = (postId) => {
    if (!user) {
      alert('请先登录才能回帖');
      return;
    }
    setCommentingId(postId);
    setCommentText('');
  };

  // 取消回帖
  const cancelComment = () => {
    setCommentingId(null);
    setCommentText('');
  };

  // 提交回帖
  const submitComment = async (postId) => {
    if (!commentText.trim()) {
      alert('回帖内容不能为空');
      return;
    }
    const res = await addComment(postId, {
      userId: user.uid,
      userEmail: user.email,
      content: commentText.trim()
    });
    if (res.success) {
      await loadPosts();
      cancelComment();
      // 自动展开评论区
      setExpandedComments(prev => ({ ...prev, [postId]: true }));
    } else {
      alert('回帖失败：' + res.error);
    }
  };

  // 删除回帖
  const removeComment = async (postId, comment) => {
    if (!confirm('确定要删除这条回帖吗？')) return;
    const res = await deleteComment(postId, comment);
    if (res.success) {
      await loadPosts();
    } else {
      alert('删除回帖失败：' + res.error);
    }
  };

  // 切换评论展开/收起
  const toggleComments = (postId) => {
    setExpandedComments(prev => ({
      ...prev,
      [postId]: !prev[postId]
    }));
  };

  // 格式化时间
  const formatDate = (timestamp) => {
    if (!timestamp) return '未知时间';
    const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
    return date.toLocaleString('zh-CN');
  };

  if (loading) {
    return (
      <div className="post-list-container">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="post-list-container">
        <div className="error-message">
          <p>加载失败：{error}</p>
          <button onClick={loadPosts} className="retry-btn">重试</button>
        </div>
      </div>
    );
  }

  return (
    <div className="post-list-container">
      <div className="post-list-header">
        <h2>消息动态</h2>
        <div className="header-controls">
          <p className="post-count">共 {posts.length} 条消息</p>
          <div className="sort-controls">
            <label>排序：</label>
            <button 
              className={`sort-btn ${sortBy === 'time' ? 'active' : ''}`}
              onClick={() => setSortBy('time')}
            >
              最新
            </button>
            <button 
              className={`sort-btn ${sortBy === 'likes' ? 'active' : ''}`}
              onClick={() => setSortBy('likes')}
            >
              最热
            </button>
            <button 
              className={`sort-btn ${sortBy === 'comments' ? 'active' : ''}`}
              onClick={() => setSortBy('comments')}
            >
              热议
            </button>
          </div>
        </div>
      </div>

      {posts.length === 0 ? (
        <div className="empty-state">
          <p>暂无消息，{user ? '发布第一条消息吧！' : '登录后可以发布消息'}</p>
        </div>
      ) : (
        <div className="posts-grid">
          {sortedPosts.map((post) => {
            const isLiked = user && post.likes?.includes(user.uid);
            const commentsCount = post.comments?.length || 0;
            const isExpanded = expandedComments[post.id];

            return (
              <div key={post.id} className="post-card">
                <div className="post-header">
                  {editingId === post.id ? (
                    <input
                      className="post-title-input"
                      value={editForm.title}
                      onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      maxLength="100"
                    />
                  ) : (
                    <h3 className="post-title">{post.title}</h3>
                  )}
                  <div className="post-meta">
                    <span className="post-author">@{post.userEmail}</span>
                    <span className="post-date">{formatDate(post.createdAt)}</span>
                  </div>
                </div>

                <div className="post-content">
                  {editingId === post.id ? (
                    <textarea
                      className="post-content-input"
                      value={editForm.content}
                      onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                      rows="4"
                      maxLength="500"
                    />
                  ) : (
                    <p className="post-text">{post.content}</p>
                  )}
                </div>

                {/* 点赞和回帖按钮 */}
                <div className="post-interactions">
                  <button 
                    className={`interaction-btn ${isLiked ? 'liked' : ''}`}
                    onClick={() => handleLike(post)}
                    disabled={!user}
                  >
                    <span className="icon">{isLiked ? '❤️' : '🤍'}</span>
                    <span className="count">{post.likesCount || 0}</span>
                  </button>
                  <button 
                    className="interaction-btn"
                    onClick={() => toggleComments(post.id)}
                  >
                    <span className="icon">💬</span>
                    <span className="count">{commentsCount}</span>
                  </button>
                  <button 
                    className="interaction-btn"
                    onClick={() => startComment(post.id)}
                    disabled={!user}
                  >
                    <span className="icon">✍️</span>
                    <span className="text">回帖</span>
                  </button>
                </div>

                {/* 回帖表单 */}
                {commentingId === post.id && (
                  <div className="comment-form">
                    <textarea
                      className="comment-input"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      placeholder="写下你的回帖..."
                      rows="2"
                      maxLength="200"
                    />
                    <div className="comment-actions">
                      <span className="char-count">{commentText.length}/200</span>
                      <div>
                        <button className="action-btn" onClick={cancelComment}>取消</button>
                        <button className="action-btn primary" onClick={() => submitComment(post.id)}>发布</button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 回帖列表 */}
                {isExpanded && commentsCount > 0 && (
                  <div className="comments-section">
                    <div className="comments-header">
                      <span>回帖 ({commentsCount})</span>
                    </div>
                    <div className="comments-list">
                      {post.comments.map((comment) => (
                        <div key={comment.id} className="comment-item">
                          <div className="comment-header">
                            <span className="comment-author">@{comment.userEmail}</span>
                            <span className="comment-date">{formatDate(comment.createdAt)}</span>
                          </div>
                          <div className="comment-content">
                            <p>{comment.content}</p>
                          </div>
                          {user && user.uid === comment.userId && (
                            <button 
                              className="comment-delete-btn"
                              onClick={() => removeComment(post.id, comment)}
                            >
                              删除
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* 编辑和删除按钮 */}
                <div className="post-footer">
                  {user && user.uid === post.userId && (
                    editingId === post.id ? (
                      <div className="edit-actions">
                        <button className="action-btn primary" onClick={() => saveEdit(post.id)}>保存</button>
                        <button className="action-btn" onClick={cancelEdit}>取消</button>
                      </div>
                    ) : (
                      <div className="edit-actions">
                        <span className="post-owner">我的消息</span>
                        <div className="edit-actions-buttons">
                          <button className="action-btn" onClick={() => startEdit(post)}>编辑</button>
                          <button className="action-btn danger" onClick={() => removePost(post.id)}>删除</button>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default PostList;

