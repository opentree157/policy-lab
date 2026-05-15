import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Datasets from "./pages/Datasets";
import ExperimentsList from "./pages/ExperimentsList";
import NewExperiment from "./pages/NewExperiment";
import ExperimentDetail from "./pages/ExperimentDetail";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/datasets" element={<Datasets />} />
        <Route path="/experiments" element={<ExperimentsList />} />
        <Route path="/experiments/new" element={<NewExperiment />} />
        <Route path="/experiments/:id" element={<ExperimentDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
