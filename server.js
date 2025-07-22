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
app.put('/api/utilisateurs/:user_id', (req, res) => {
  console.log('Mise à jour utilisateur ID:', req.params.user_id);
  console.log('Données reçues:', req.body);

  const { nom, langue, montant_depot, benefice_total, commissions_totales, adresse_wallet, cycle, statut, date_enregistrement, date_mise_a_jour } = req.body;
  const { user_id } = req.params;

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
    user_id
  ];

  console.log('Paramètres SQL:', params);

  db.run(query, params, function (err) {
    if (err) {
      console.error('Erreur SQL:', err.message);
      return res.status(500).json({ error: 'Erreur serveur lors de la mise à jour' });
    }

    if (this.changes === 0) {
      console.log('Aucune ligne modifiée - utilisateur non trouvé');
      return res.status(404).json({ error: 'Utilisateur non trouvé' });
    }

    console.log('Succès - lignes modifiées:', this.changes);
    res.status(200).json({ message: 'Utilisateur mis à jour avec succès' });
  });
});
// Route pour modifier uniquement le statut d'un utilisateur
app.patch('/api/utilisateurs/:id/statut', (req, res) => {
  console.log('Modification statut utilisateur ID:', req.params.id);
  console.log('Nouveau statut:', req.body);

  const { id } = req.params;
  const { statut } = req.body;

  // Validation du statut
  if (!statut || !['actif', 'inactif'].includes(statut)) {
    console.log('Statut invalide:', statut);
    return res.status(400).json({ error: 'Statut invalide. Doit être "actif" ou "inactif"' });
  }

  const query = 'UPDATE utilisateurs SET statut = ? WHERE user_id = ?';
  
  console.log('Exécution requête SQL:', query);
  console.log('Paramètres:', [statut, id]);

  db.run(query, [statut, id], function (err) {
    if (err) {
      console.error('Erreur SQL:', err.message);
      return res.status(500).json({ error: 'Erreur serveur lors de la mise à jour du statut' });
    }

    if (this.changes === 0) {
      console.log('Aucune ligne modifiée - utilisateur non trouvé');
      return res.status(404).json({ error: 'Utilisateur non trouvé' });
    }

    console.log('Statut mis à jour avec succès - lignes modifiées:', this.changes);
    res.status(200).json({ 
      message: 'Statut mis à jour avec succès',
      statut: statut,
      user_id: id
    });
  });
});
// Route pour ajouter un utilisateur
// Route pour ajouter un utilisateur avec user_id personnalisé
app.post('/api/utilisateurs', (req, res) => {
  console.log('Requête reçue pour POST /api/utilisateurs');
  console.log('Données reçues:', req.body);
  
  const { user_id, parrain_id, nom, langue, adresse_wallet, statut } = req.body;
  
  // Validation des champs obligatoires
  if (!user_id || !nom || !langue) {
    return res.status(400).json({ 
      error: 'Les champs user_id, nom et langue sont obligatoires' 
    });
  }

  // Validation du format de user_id (optionnel - ajustez selon vos besoins)
  if (typeof user_id !== 'string' && typeof user_id !== 'number') {
    return res.status(400).json({ 
      error: 'Le user_id doit être une chaîne de caractères ou un nombre' 
    });
  }

  // Valeurs par défaut
  const dateActuelle = new Date().toISOString();
  const benefice_total = 0;
  const commissions_totales = 0;
  const montant_depot = null;
  const cycle = null;
  const statutFinal = statut || 'actif';

  // Vérifier d'abord si l'user_id existe déjà
  const checkQuery = 'SELECT user_id FROM utilisateurs WHERE user_id = ?';
  
  db.get(checkQuery, [user_id], (err, row) => {
    if (err) {
      console.error('Erreur lors de la vérification de l\'user_id:', err.message);
      return res.status(500).json({ 
        error: 'Erreur serveur lors de la vérification' 
      });
    }
    
    if (row) {
      return res.status(409).json({ 
        error: 'Un utilisateur avec cet user_id existe déjà' 
      });
    }

    // Insérer le nouvel utilisateur avec l'user_id personnalisé
    const insertQuery = `
      INSERT INTO utilisateurs 
      (user_id, parrain_id, nom, langue, montant_depot, benefice_total, commissions_totales, 
       date_enregistrement, adresse_wallet, date_mise_a_jour, cycle, statut)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    
    const params = [
      user_id,
      parrain_id || null,
      nom,
      langue,
      montant_depot,
      benefice_total,
      commissions_totales,
      dateActuelle,
      adresse_wallet || null,
      dateActuelle,
      cycle,
      statutFinal
    ];

    console.log('Paramètres SQL:', params);

    db.run(insertQuery, params, function (err) {
      if (err) {
        console.error('Erreur SQL:', err.message);
        // Gestion spécifique des erreurs de contrainte
        if (err.message.includes('UNIQUE constraint failed')) {
          return res.status(409).json({ 
            error: 'Un utilisateur avec cet user_id existe déjà' 
          });
        }
        return res.status(500).json({ 
          error: 'Erreur serveur lors de la création de l\'utilisateur' 
        });
      }

      console.log('Utilisateur créé avec succès - ID:', user_id);
      res.status(201).json({ 
        message: 'Utilisateur créé avec succès',
        user_id: user_id,
        data: {
          user_id: user_id,
          parrain_id: parrain_id || null,
          nom,
          langue,
          montant_depot,
          benefice_total,
          commissions_totales,
          date_enregistrement: dateActuelle,
          adresse_wallet: adresse_wallet || null,
          date_mise_a_jour: dateActuelle,
          cycle,
          statut: statutFinal
        }
      });
    });
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