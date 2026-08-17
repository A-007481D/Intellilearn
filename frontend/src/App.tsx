import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Chat from './pages/Chat';
import Quizzes from './pages/Quizzes';
import Admin from './pages/Admin';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Navigate to="/documents" replace />} />
        <Route path="/documents" element={
          <ProtectedRoute><Layout><Documents /></Layout></ProtectedRoute>
        } />
        <Route path="/chat" element={
          <ProtectedRoute><Layout><Chat /></Layout></ProtectedRoute>
        } />
        <Route path="/quizzes" element={
          <ProtectedRoute><Layout><Quizzes /></Layout></ProtectedRoute>
        } />
        <Route path="/dashboard" element={
          <ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute><Layout><Admin /></Layout></ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
