import { Navigate } from 'react-router-dom';
import AuthLayout from '../layouts/AuthLayout';
import SignupForm from '../components/auth/SignupForm';
import { useAuth } from '../context/AuthContext';

const SignUpPage = () => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <AuthLayout>
      <SignupForm />
    </AuthLayout>
  );
};

export default SignUpPage;