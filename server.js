const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Connexion à la base de données
const dbPath = path.join(__dirname, 'bot.db'); // Remplacez par le chemin de votre BD
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Erreur de connexion à la base de données:', err.message);
  } else {
    console.log('Connecté à la base de données SQLite');
  }
});

// Routes pour les utilisateurs
app.get('/api/utilisateurs', (req, res) => {
  console.log('Requête reçue pour /api/utilisateurs');

  const query = `
    SELECT 
      user_id, parrain_id, nom, langue, montant_depot, 
      benefice_total, commissions_totales, date_enregistrement, 
      adresse_wallet, date_mise_a_jour, cycle, statut 
    FROM utilisateurs 
    ORDER BY date_enregistrement DESC
  `;
  
  db.all(query, (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

app.get('/api/utilisateurs/:id', (req, res) => {
    console.log('Requête reçue pour /api/utilisateurs/:id');

  const { id } = req.params;
  const query = 'SELECT * FROM utilisateurs WHERE user_id = ?';
  
  db.get(query, [id], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (!row) {
      return res.status(404).json({ error: 'Utilisateur non trouvé' });
    }
    res.json(row);
  });
});

// Route pour supprimer un utilisateur
app.delete('/api/utilisateurs/:id', (req, res) => {
    console.log('Requête reçue pour delete /api/utilisateurs');

  const { id } = req.params;
  const query = 'DELETE FROM utilisateurs WHERE user_id = ?';
  
  db.run(query, [id], function(err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (this.changes === 0) {
      return res.status(404).json({ error: 'Utilisateur non trouvé' });
    }
    res.json({ message: 'Utilisateur supprimé avec succès' });
  });
});

// Route pour modifier un utilisateur
app.put('/update-user/:id', (req, res) => {
  const { nom, langue, montant_depot, benefice_total, commissions_totales, adresse_wallet, cycle, statut, date_enregistrement,date_mise_a_jour } = req.body;
  const { id } = req.params;

  // Formatage automatique de la date de mise à jour
  // const date_mise_a_jour = new Date().toISOString().slice(0, 19).replace('T', ' ');

  const query = `
    UPDATE utilisateurs 
    SET nom = ?, 
        langue = ?, 
        montant_depot = ?, 
        benefice_total = ?, 
        commissions_totales = ?, 
        adresse_wallet = ?, 
        cycle = ?, 
        statut = ?, 
        date_enregistrement = ?, 
        date_mise_a_jour = ?
    WHERE user_id = ?
  `;

  const params = [
    nom,
    langue,
    montant_depot,
    benefice_total,
    commissions_totales,
    adresse_wallet,
    cycle,
    statut,
    date_enregistrement,
    date_mise_a_jour,
    id
  ];

  console.log('Paramètres pour mise à jour :', params); // Debug

  db.run(query, params, function (err) {
    if (err) {
      console.error('Erreur lors de la mise à jour :', err.message);
      return res.status(500).json({ error: 'Erreur serveur lors de la mise à jour' });
    }

    if (this.changes === 0) {
      return res.status(404).json({ error: 'Utilisateur non trouvé' });
    }

    res.status(200).json({ message: 'Utilisateur mis à jour avec succès' });
  });
});

// Routes pour les retraits
app.get('/api/retraits', (req, res) => {
    console.log('Requête reçue pour /api/retrait');

  const query = `
    SELECT r.*, u.nom 
    FROM retraits r 
    LEFT JOIN utilisateurs u ON r.user_id = u.user_id 
    ORDER BY r.date_retrait DESC
  `;
  
  db.all(query, (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

app.get('/api/retraits/user/:userId', (req, res) => {
      console.log('Requête reçue pour /api/retrait/:userid');

  const { userId } = req.params;
  const query = 'SELECT * FROM retraits WHERE user_id = ? ORDER BY date_retrait DESC';
  
  db.all(query, [userId], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Routes pour les dépôts
app.get('/api/depot', (req, res) => {
      console.log('Requête reçue pour /api/depot');

  const query = `
    SELECT d.*, u.nom 
    FROM depot d 
    LEFT JOIN utilisateurs u ON d.user_id = u.user_id 
    ORDER BY d.date_depot DESC
  `;
  
  db.all(query, (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

app.get('/api/depot/user/:userId', (req, res) => {
  console.log('Requête reçue pour /api/depot/:userid');

  const { userId } = req.params;
  const query = 'SELECT * FROM depot WHERE user_id = ? ORDER BY date_depot DESC';
  
  db.all(query, [userId], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Routes pour les commissions
app.get('/api/commissions', (req, res) => {
        console.log('Requête reçue pour /api/commissions');

  const query = `
    SELECT 
      c.*, 
      u1.nom as parrain_nom, 
      u2.nom as filleul_nom
    FROM commissions c
    LEFT JOIN utilisateurs u1 ON c.user_id = u1.user_id
    LEFT JOIN utilisateurs u2 ON c.filleul_id = u2.user_id
    ORDER BY c.date DESC
  `;
  
  db.all(query, (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

app.get('/api/commissions/user/:userId', (req, res) => {
          console.log('Requête reçue pour /api/commissions/:userid');

  const { userId } = req.params;
  const query = `
    SELECT 
      c.*, 
      u.nom as filleul_nom
    FROM commissions c
    LEFT JOIN utilisateurs u ON c.filleul_id = u.user_id
    WHERE c.user_id = ? 
    ORDER BY c.date DESC
  `;
  
  db.all(query, [userId], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Route pour les statistiques générales
app.get('/api/stats', (req, res) => {
          console.log('Requête reçue pour /api/stat');

  const queries = {
    totalUsers: 'SELECT COUNT(*) as count FROM utilisateurs',
    totalDeposits: 'SELECT SUM(montant_depot) as total FROM utilisateurs',
    totalWithdrawals: 'SELECT SUM(montant) as total FROM retraits',
    totalCommissions: 'SELECT SUM(montant) as total FROM commissions'
  };

  const stats = {};
  let completed = 0;
  const totalQueries = Object.keys(queries).length;

  Object.entries(queries).forEach(([key, query]) => {
    db.get(query, (err, row) => {
      if (err) {
        stats[key] = { error: err.message };
      } else {
        stats[key] = row;
      }
      
      completed++;
      if (completed === totalQueries) {
        res.json(stats);
      }
    });
  });
});

// Route pour la hiérarchie (parrains/filleuls)
app.get('/api/hierarchy/:userId', (req, res) => {
            console.log('Requête reçue pour /api/hierarchy/:userid');

  const { userId } = req.params;
  
  // Récupérer les filleuls
  const query = `
    SELECT user_id, nom, montant_depot, date_enregistrement, statut
    FROM utilisateurs 
    WHERE parrain_id = ?
    ORDER BY date_enregistrement DESC
  `;
  
  db.all(query, [userId], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Gestion des erreurs
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Erreur interne du serveur' });
});

// Démarrage du serveur
app.listen(PORT, () => {
  console.log(`Serveur démarré sur le port ${PORT}`);
});

// Fermeture propre de la base de données
process.on('SIGINT', () => {
  db.close((err) => {
    if (err) {
      console.error(err.message);
    }
    console.log('Connexion à la base de données fermée');
    process.exit(0);
  });
});