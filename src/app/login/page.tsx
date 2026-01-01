'use client'
import React, { useState } from 'react';
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  GoogleAuthProvider
} from 'firebase/auth';
import { auth } from '../../../firebase-config';
import { useRouter } from 'next/navigation';
import Navbar from '../components/Navbar';

interface LoginProps { }

const Login: React.FC<LoginProps> = () => {
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');
  const [rememberMe, setRememberMe] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [isSignUp, setIsSignUp] = useState<boolean>(false);
  


  // Password validation function
  const validatePassword = (pwd: string): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];

    if (pwd.length < 8) {
      errors.push('At least 8 characters long');
    }
    if (!/[A-Z]/.test(pwd)) {
      errors.push('At least 1 uppercase letter');
    }
    if (!/[a-z]/.test(pwd)) {
      errors.push('At least 1 lowercase letter');
    }
    if (!/\d/.test(pwd)) {
      errors.push('At least 1 number');
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)) {
      errors.push('At least 1 special character');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  };

  const router = useRouter();

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      setError(`Password must have: ${passwordValidation.errors.join(', ')}`);
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      await fetch('http://localhost:8000/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid: user.uid,
          email: user.email,
          displayName: displayName,
          photoURL: user.photoURL,
        }),
      });

      router.push('/git-to-docs'); // Redirect after signup

    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      await fetch('http://localhost:8000/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
        }),
      });

      router.push('/git-to-docs'); // Redirect after login

    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const provider = new GoogleAuthProvider();
      const userCredential = await signInWithPopup(auth, provider);
      const user = userCredential.user;

      await fetch('http://localhost:8000/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
        }),
      });

      router.push('/git-to-docs');

    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      setError('Please enter your email address first');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await sendPasswordResetEmail(auth, email);
      setSuccess('Password reset email sent! Check your inbox.');
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsSignUp(!isSignUp);
    setError('');
    setSuccess('');
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setDisplayName('');
  };

  return (
    <>
      <style jsx>{`
        .brand-color {
          background-color: #3B1C32;
        }
        .brand-text {
          color: #3B1C32;
        }
        .brand-focus:focus {
          box-shadow: 0 0 0 2px #3B1C32;
          border-color: transparent;
        }
        .brand-hover:hover {
          color: #2A1426;
        }
        .checkbox-brand {
          accent-color: #3B1C32;
        }
        .gradient-bg {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .login-container {
          background: linear-gradient(135deg, rgba(59, 28, 50, 0.1) 0%, rgba(255, 255, 255, 0.95) 50%, rgba(102, 126, 234, 0.1) 100%);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
      `}</style>

      <div className="min-h-screen flex items-center justify-center p-4 gradient-bg">
        <Navbar/>
        <div className="flex login-container rounded-3xl shadow-2xl m-8 overflow-hidden max-w-6xl w-full h-[700px]">
          {/* Left Side - Image Section */}
          <div className="flex-1 relative hidden lg:flex flex-col justify-center items-center overflow-hidden">
            <div className="w-full h-full flex items-center justify-center">
              <img
                src="/3847762.jpg"
                alt="Login Background"
                className="w-full h-full object-cover"
                onError={(e) => {
                  console.log('Image failed to load');
                  e.currentTarget.style.display = 'none';
                }}
                onLoad={() => console.log('Image loaded successfully')}
              />
              {/* Fallback gradient if image doesn't load */}
              {/* <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-pink-600 to-blue-600 opacity-80"></div> */}
              <div className="absolute inset-0 flex flex-col justify-between p-8 text-white z-10">
                <div>
                  <span className="text-sm font-light tracking-wider opacity-80">A WISE QUOTE</span>
                </div>
                
              </div>
            </div>
          </div>

          {/* Right Side - Login/SignUp Form */}
          <div className="flex-1 p-8 flex flex-col justify-center max-w-md mx-auto w-full bg-white bg-opacity-90 backdrop-blur-sm h-full overflow-y-auto">
            {/* Logo */}
            <div className="mb-6 flex-shrink-0">
              <div className="flex items-center justify-center lg:justify-start">
                <span className="text-xl font-semibold text-black">GIT2DOCS</span>
              </div>
            </div>

            {/* Welcome Back / Create Account */}
            <div className="mb-6 flex-shrink-0">
              <h2 className="text-3xl font-bold text-black mb-2">
                {isSignUp ? 'Create Account' : 'Welcome Back'}
              </h2>
              <p className="text-gray-600 text-sm">
                {isSignUp
                  ? 'Enter your details to create your account'
                  : 'Enter your email and password to access your account'
                }
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-300 text-red-700 rounded-lg text-sm flex-shrink-0">
                {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="mb-4 p-3 bg-green-50 border border-green-300 text-green-700 rounded-lg text-sm flex-shrink-0">
                {success}
              </div>
            )}

            {/* Form Container with fixed height */}
            <div className="flex-1 flex flex-col justify-center min-h-0">
              <form onSubmit={isSignUp ? handleSignUp : handleSignIn} className="space-y-4">
                {/* Display Name (Sign Up only) */}
                <div className={`transition-all duration-300 ${isSignUp ? 'opacity-100 max-h-20' : 'opacity-0 max-h-0 overflow-hidden'}`}>
                  <label htmlFor="displayName" className="block text-sm font-medium text-black mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    id="displayName"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Enter your full name"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg brand-focus outline-none transition-all placeholder-gray-500 text-black bg-white text-sm"
                    required={isSignUp}
                  />
                </div>

                {/* Email Field */}
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-black mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg brand-focus outline-none transition-all placeholder-gray-500 text-black bg-white text-sm"
                    required
                  />
                </div>

                {/* Password Field */}
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-black mb-1">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      id="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-lg brand-focus outline-none transition-all placeholder-gray-500 text-black bg-white text-sm"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-600 hover:text-black transition-colors"
                    >
                      {showPassword ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                        </svg>
                      )}
                    </button>
                  </div>
                  {/* Password Requirements (Sign Up only) - Compact */}
                  <div className={`transition-all duration-300 ${isSignUp && password ? 'opacity-100 max-h-16 mt-2' : 'opacity-0 max-h-0 overflow-hidden'}`}>
                    <div className="text-xs grid grid-cols-2 gap-1">
                      <div className={`${password.length >= 8 ? 'text-green-600' : 'text-red-600'}`}>
                        ✓ 8+ chars
                      </div>
                      <div className={`${/[A-Z]/.test(password) ? 'text-green-600' : 'text-red-600'}`}>
                        ✓ Uppercase
                      </div>
                      <div className={`${/[a-z]/.test(password) ? 'text-green-600' : 'text-red-600'}`}>
                        ✓ Lowercase
                      </div>
                      <div className={`${/\d/.test(password) ? 'text-green-600' : 'text-red-600'}`}>
                        ✓ Number
                      </div>
                      <div className={`${/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password) ? 'text-green-600' : 'text-red-600'} col-span-2`}>
                        ✓ Special character
                      </div>
                    </div>
                  </div>
                </div>

                {/* Confirm Password (Sign Up only) */}
                <div className={`transition-all duration-300 ${isSignUp ? 'opacity-100 max-h-24' : 'opacity-0 max-h-0 overflow-hidden'}`}>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-black mb-1">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      id="confirmPassword"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm your password"
                      className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-lg brand-focus outline-none transition-all placeholder-gray-500 text-black bg-white text-sm"
                      required={isSignUp}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-600 hover:text-black transition-colors"
                    >
                      {showConfirmPassword ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                        </svg>
                      )}
                    </button>
                  </div>
                  {confirmPassword && password !== confirmPassword && (
                    <p className="mt-1 text-xs text-red-600">Passwords do not match</p>
                  )}
                </div>

                {/* Remember Me & Forgot Password (Sign In only) */}
                <div className={`transition-all duration-300 ${!isSignUp ? 'opacity-100 max-h-10' : 'opacity-0 max-h-0 overflow-hidden'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="remember"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="w-4 h-4 border-gray-300 rounded text-black checkbox-brand"
                      />
                      <label htmlFor="remember" className="ml-2 text-sm text-black">
                        Remember me
                      </label>
                    </div>
                    <button
                      type="button"
                      onClick={handleForgotPassword}
                      className="text-sm font-medium brand-text brand-hover transition-colors"
                      disabled={loading}
                    >
                      Forgot Password?
                    </button>
                  </div>
                </div>

                {/* Sign In/Up Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    {loading ? (isSignUp ? 'Creating Account...' : 'Signing In...') : (isSignUp ? 'Create Account' : 'Sign In')}
                  </button>

                  {/* Google Sign In */}
                  <button
                    type="button"
                    onClick={handleGoogleLogin}
                    disabled={loading}
                    className="w-full border border-gray-300 py-2.5 rounded-lg font-medium hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-black bg-white mt-3 text-sm"
                  >
                    <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    {isSignUp ? 'Sign Up with Google' : 'Sign In with Google'}
                  </button>
                </div>
              </form>
            </div>

            {/* Toggle Sign In/Up */}
            <div className="mt-6 text-center flex-shrink-0">
              <span className="text-gray-600 text-sm">
                {isSignUp ? 'Already have an account? ' : "Don't have an account? "}
              </span>
              <button
                onClick={switchMode}
                className="font-medium brand-text brand-hover transition-colors text-sm"
              >
                {isSignUp ? 'Sign In' : 'Sign Up'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Login;