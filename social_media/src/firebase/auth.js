// Firebase认证服务
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  GoogleAuthProvider
} from 'firebase/auth';
import { auth } from './config';

/**
 * 用户注册
 * @param {string} email - 用户邮箱
 * @param {string} password - 用户密码
 * @returns {Promise} 注册结果
 */
export const registerUser = async (email, password) => {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    return { success: true, user: userCredential.user };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

/**
 * 用户登录
 * @param {string} email - 用户邮箱
 * @param {string} password - 用户密码
 * @returns {Promise} 登录结果
 */
export const loginUser = async (email, password) => {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return { success: true, user: userCredential.user };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

/**
 * 用户登出
 * @returns {Promise} 登出结果
 */
export const logoutUser = async () => {
  try {
    await signOut(auth);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

/**
 * Google登录（使用重定向方式）
 * @returns {Promise} 登录结果
 */
export const loginWithGoogle = async () => {
  try {
    const provider = new GoogleAuthProvider();
    // 设置额外的OAuth参数
    provider.setCustomParameters({
      prompt: 'select_account'
    });
    
    // 改回弹窗登录方式
    const result = await signInWithPopup(auth, provider);
    return { success: true, user: result.user };
  } catch (error) {
    console.error('Google登录失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 处理Google登录重定向结果
 * @returns {Promise} 登录结果
 */
export const handleGoogleRedirect = async () => {
  try {
    const result = await getRedirectResult(auth);
    if (result && result.user) {
      return { success: true, user: result.user };
    }
    return { success: false, message: '没有重定向结果' };
  } catch (error) {
    console.error('处理Google重定向失败:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 监听用户认证状态变化
 * @param {Function} callback - 状态变化回调函数
 * @returns {Function} 取消监听的函数
 */
export const onAuthStateChange = (callback) => {
  return onAuthStateChanged(auth, callback);
};
