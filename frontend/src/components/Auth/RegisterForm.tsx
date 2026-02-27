import React, { useState } from 'react';
import { register, login, saveToken } from '../../services/auth';

interface Props {
  onSuccess: () => void;
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<Props> = ({ onSuccess, onSwitchToLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await register({ username, password });
      // Auto-login after successful registration
      const loginRes = await login({ username, password });
      saveToken(loginRes.access_token);
      onSuccess();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-form">
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username:</label>
          <input type="text" value={username} onChange={e => setUsername(e.target.value)} required />
        </div>
        <div>
          <label>Password:</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>
        {error && <div className="error">{error}</div>}
        <button type="submit">Register</button>
      </form>
      <p>Already have an account? <button onClick={onSwitchToLogin}>Login</button></p>
    </div>
  );
};