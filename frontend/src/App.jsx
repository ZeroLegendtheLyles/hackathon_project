import { Routes, Route } from "react-router-dom";
import "./App.css";
import Navbar from "./components/Navbar/Navbar";
import Home from "./pages/Home/Home";
import Menu from "./pages/Menu/Menu";
import About from "./pages/About/About";
import Metrics from "./pages/Metrics/Metrics";
import Admin from "./pages/Admin/Admin";

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/menu" element={<Menu />} />
        <Route path="/about" element={<About />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/metrics" element={<Metrics />} />
      </Routes>
    </>
  );
}

export default App;
