import { lazy, Suspense } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";

const Homepage = lazy(() => import("./pages/Home/Homepage"));
const Login = lazy(() => import("./pages/Auth/Login"));
const Signup = lazy(() => import("./pages/Auth/Signup"));

const UserLayout = lazy(() => import("./layouts/UserLayout"));
const UserDashboard = lazy(() => import("./pages/Dashboard/UserDashboard"));
const WalletPage = lazy(() => import("./pages/Wallet & Payment/WalletPage"));
const RechargeWallet = lazy(() => import("./pages/Wallet & Payment/RechargeWallet/RechargeWallet"));
const TripHistory = lazy(() => import("./pages/Trips/User/TripHistory"));
const ProfilePage = lazy(() => import("./pages/Profile & settings/ProfilePage"));
const EditProfile = lazy(() => import("./pages/Profile & settings/EditProfile"));
const AddVehicle = lazy(() => import("./pages/Profile & settings/AddVehicle/AddVehicle"));
const PlateScan = lazy(() => import("./pages/PlateScan/PlateScan"));

const AdminLayout = lazy(() => import("./layouts/AdminLayout"));
const AdminDashboard = lazy(() => import("./pages/Dashboard/AdminDashboard"));
const Admin_Trip = lazy(() => import("./pages/Trips/Admin_Trip/Admin_Trip"));
const Admin_Wallet = lazy(() => import("./pages/Wallet/Admin_Wallet/Admin_Wallet"));

function RouteFallback() {
  return <div className="route-fallback" aria-hidden />;
}

function App() {
  return (
    <Router>
      <div className="App">
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/" element={<Homepage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            <Route path="/dashboard" element={<UserLayout />}>
              <Route index element={<UserDashboard />} />
              <Route path="wallet" element={<WalletPage />} />
              <Route path="wallet/recharge" element={<RechargeWallet />} />
              <Route path="trips" element={<TripHistory />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="profile/edit" element={<EditProfile />} />
              <Route path="profile/add-vehicle" element={<AddVehicle />} />
            </Route>

            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<AdminDashboard />} />
              <Route path="trips" element={<Admin_Trip />} />
              <Route path="wallet" element={<Admin_Wallet />} />
              <Route path="plate-scan" element={<PlateScan adminMode />} />
            </Route>
          </Routes>
        </Suspense>
      </div>
    </Router>
  );
}

export default App;
