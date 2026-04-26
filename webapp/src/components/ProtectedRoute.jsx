import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { user } = useAuth();

  // If there's no user, redirect to the login page
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If the route requires admin but the user is not an admin, redirect to dashboard
  if (requireAdmin && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  // If children are provided, render them, otherwise render the nested routes (Outlet)
  return children ? children : <Outlet />;
};
