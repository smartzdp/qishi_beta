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
  updateDoc 
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
 * 添加图书到数据库
 * @param {Object} bookData - 图书数据
 * @param {string} bookData.title - 图书标题
 * @param {string} bookData.description - 图书简介
 * @param {string} bookData.userId - 用户ID
 * @param {string} bookData.userEmail - 用户邮箱
 * @returns {Promise} 添加结果
 */
export const addBook = async (bookData) => {
  try {
    console.log('开始添加图书:', bookData);
    const docRef = await addDoc(collection(db, 'books'), {
      ...bookData,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp()
    });
    console.log('图书添加成功，ID:', docRef.id);
    return { success: true, id: docRef.id };
  } catch (error) {
    console.error('添加图书失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 获取所有图书列表
 * @returns {Promise} 图书列表
 */
export const getAllBooks = async () => {
  try {
    console.log('开始获取图书列表...');
    const q = query(collection(db, 'books'), orderBy('createdAt', 'desc'));
    const querySnapshot = await getDocs(q);
    const books = [];
    querySnapshot.forEach((doc) => {
      books.push({
        id: doc.id,
        ...doc.data()
      });
    });
    console.log('成功获取图书列表:', books.length, '本图书');
    return { success: true, books };
  } catch (error) {
    console.error('获取图书列表失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 获取特定用户的图书列表
 * @param {string} userId - 用户ID
 * @returns {Promise} 用户图书列表
 */
export const getUserBooks = async (userId) => {
  try {
    const q = query(
      collection(db, 'books'), 
      where('userId', '==', userId),
      orderBy('createdAt', 'desc')
    );
    const querySnapshot = await getDocs(q);
    const books = [];
    querySnapshot.forEach((doc) => {
      books.push({
        id: doc.id,
        ...doc.data()
      });
    });
    return { success: true, books };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

/**
 * 更新图书信息（仅允许拥有者在前端触发）
 * @param {string} bookId - 文档ID
 * @param {{title?: string, description?: string}} updates - 更新字段
 * @returns {Promise<{success:boolean, error?:string}>}
 */
export const updateBook = async (bookId, updates) => {
  try {
    const ref = doc(db, 'books', bookId);
    await updateDoc(ref, {
      ...updates,
      updatedAt: serverTimestamp()
    });
    return { success: true };
  } catch (error) {
    console.error('更新图书失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 删除图书（仅允许拥有者在前端触发）
 * @param {string} bookId - 文档ID
 * @returns {Promise<{success:boolean, error?:string}>}
 */
export const deleteBook = async (bookId) => {
  try {
    const ref = doc(db, 'books', bookId);
    const { deleteField } = await import('firebase/firestore'); // 占位以确保tree-shaking
    // 实际删除
    const { deleteDoc } = await import('firebase/firestore');
    await deleteDoc(ref);
    return { success: true };
  } catch (error) {
    console.error('删除图书失败:', error);
    return { success: false, error: error.message };
  }
};
