// src/components/Landing/Landing.jsx
import React from "react";
import { Link } from "react-router-dom";

import adminImg from "../../assets/admin.png";
import userImg from "../../assets/user.png";

import "./Home.css";

const Home = () => {
  return (
    <div className="landing-wrap">
      <div className="landing-row">
        <Link to="/admin-login" className="landing-card" aria-label="Sign in as Admin">
          <div className="landing-image-wrap">
            <img src={adminImg} alt="Admin sign in" className="landing-image" />
          </div>
          <div className="landing-caption">Sign in as Admin</div>
        </Link>

        <Link to="/user-login" className="landing-card" aria-label="Sign in as User">
          <div className="landing-image-wrap">
            <img src={userImg} alt="User sign in" className="landing-image" />
          </div>
          <div className="landing-caption">Sign in as User</div>
        </Link>
      </div>
    </div>
  );
};

export default Home;
