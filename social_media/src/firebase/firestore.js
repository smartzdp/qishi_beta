// Firestore数据库服务
import { 
  collection, 
  addDoc, 
  getDocs, 
  query, 
  orderBy, 
  where,
  serverTimestamp,
  doc,
  updateDoc,
  arrayUnion,
  arrayRemove,
  increment
} from 'firebase/firestore';
import { db } from './config';

/**
 * 测试Firestore连接
 * @returns {Promise} 测试结果
 */
export const testFirestoreConnection = async () => {
  try {
    console.log('测试Firestore连接...');
    const testCollection = collection(db, 'test');
    const querySnapshot = await getDocs(testCollection);
    console.log('Firestore连接测试成功');
    return { success: true, message: 'Firestore连接正常' };
  } catch (error) {
    console.error('Firestore连接测试失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 添加消息到数据库
 * @param {Object} postData - 消息数据
 * @param {string} postData.title - 消息标题
 * @param {string} postData.content - 消息内容
 * @param {string} postData.userId - 用户ID
 * @param {string} postData.userEmail - 用户邮箱
 * @returns {Promise} 添加结果
 */
export const addPost = async (postData) => {
  try {
    console.log('开始添加消息:', postData);
    const docRef = await addDoc(collection(db, 'posts'), {
      ...postData,
      likes: [],        // 点赞用户ID数组
      likesCount: 0,    // 点赞数
      comments: [],     // 回帖数组
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp()
    });
    console.log('消息添加成功，ID:', docRef.id);
    return { success: true, id: docRef.id };
  } catch (error) {
    console.error('添加消息失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 获取所有消息列表
 * @returns {Promise} 消息列表
 */
export const getAllPosts = async () => {
  try {
    console.log('开始获取消息列表...');
    const q = query(collection(db, 'posts'), orderBy('createdAt', 'desc'));
    const querySnapshot = await getDocs(q);
    const posts = [];
    querySnapshot.forEach((doc) => {
      posts.push({
        id: doc.id,
        ...doc.data()
      });
    });
    console.log('成功获取消息列表:', posts.length, '条消息');
    return { success: true, posts };
  } catch (error) {
    console.error('获取消息列表失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 获取特定用户的消息列表
 * @param {string} userId - 用户ID
 * @returns {Promise} 用户消息列表
 */
export const getUserPosts = async (userId) => {
  try {
    const q = query(
      collection(db, 'posts'), 
      where('userId', '==', userId),
      orderBy('createdAt', 'desc')
    );
    const querySnapshot = await getDocs(q);
    const posts = [];
    querySnapshot.forEach((doc) => {
      posts.push({
        id: doc.id,
        ...doc.data()
      });
    });
    return { success: true, posts };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

/**
 * 更新消息信息（仅允许拥有者在前端触发）
 * @param {string} postId - 文档ID
 * @param {{title?: string, content?: string}} updates - 更新字段
 * @returns {Promise<{success:boolean, error?:string}>}
 */
export const updatePost = async (postId, updates) => {
  try {
    const ref = doc(db, 'posts', postId);
    await updateDoc(ref, {
      ...updates,
      updatedAt: serverTimestamp()
    });
    return { success: true };
  } catch (error) {
    console.error('更新消息失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 删除消息（仅允许拥有者在前端触发）
 * @param {string} postId - 文档ID
 * @returns {Promise<{success:boolean, error?:string}>}
 */
export const deletePost = async (postId) => {
  try {
    const ref = doc(db, 'posts', postId);
    const { deleteField } = await import('firebase/firestore'); // 占位以确保tree-shaking
    // 实际删除
    const { deleteDoc } = await import('firebase/firestore');
    await deleteDoc(ref);
    return { success: true };
  } catch (error) {
    console.error('删除消息失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 点赞或取消点赞消息
 * @param {string} postId - 消息ID
 * @param {string} userId - 用户ID
 * @param {boolean} isLiked - 当前是否已点赞
 * @returns {Promise<{success:boolean, error?:string}>}
 */
export const toggleLike = async (postId, userId, isLiked) => {
  try {
    const ref = doc(db, 'posts', postId);
    if (isLiked) {
      // 取消点赞
      await updateDoc(ref, {
        likes: arrayRemove(userId),
        likesCount: increment(-1),
        updatedAt: serverTimestamp()
      });
    } else {
      // 点赞
      await updateDoc(ref, {
        likes: arrayUnion(userId),
        likesCount: increment(1),
        updatedAt: serverTimestamp()
      });
    }
    return { success: true };
  } catch (error) {
    console.error('点赞操作失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 添加回帖
 * @param {string} postId - 消息ID
 * @param {Object} commentData - 回帖数据
 * @param {string} commentData.userId - 用户ID
 * @param {string} commentData.userEmail - 用户邮箱
 * @param {string} commentData.content - 回帖内容
 * @returns {Promise<{success:boolean, error?:string}>}
 */
export const addComment = async (postId, commentData) => {
  try {
    const ref = doc(db, 'posts', postId);
    const comment = {
      id: Date.now().toString(), // 使用时间戳作为简单ID
      ...commentData,
      createdAt: new Date().toISOString()
    };
    await updateDoc(ref, {
      comments: arrayUnion(comment),
      updatedAt: serverTimestamp()
    });
    return { success: true, comment };
  } catch (error) {
    console.error('添加回帖失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 删除回帖
 * @param {string} postId - 消息ID
 * @param {Object} comment - 要删除的回帖对象
 * @returns {Promise<{success:boolean, error?:string}>}
 */
export const deleteComment = async (postId, comment) => {
  try {
    const ref = doc(db, 'posts', postId);
    await updateDoc(ref, {
      comments: arrayRemove(comment),
      updatedAt: serverTimestamp()
    });
    return { success: true };
  } catch (error) {
    console.error('删除回帖失败:', error);
    return { success: false, error: error.message };
  }
};
