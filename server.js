const express = require("express");
const dotenv = require("dotenv");
const cors = require("cors");

dotenv.config();
const app = express();
app.use(express.json());
app.use(cors());

// Importando rotas
const authRoutes = require("./routes/auth");
const userRoutes = require("./routes/users");
const appointmentRoutes = require("./routes/appointments");
const medicalRecordRoutes = require("./routes/medicalRecords");

// **Endpoint de teste**
app.get("/", (req, res) => {
    res.send("🚀 Backend funcionando!");
});

app.use("/auth", authRoutes);
app.use("/users", userRoutes);
app.use("/appointments", appointmentRoutes);
app.use("/medical-records", medicalRecordRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ Servidor rodando na porta ${PORT}`);
});
