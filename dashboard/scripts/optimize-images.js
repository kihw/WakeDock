/**
 * Script d'optimisation des images
 * Convertit automatiquement les images en WebP et les optimise
 */

import { readdir, stat } from 'fs/promises';
import { join, extname } from 'path';
import { execSync } from 'child_process';

// Assurez-vous d'installer sharp via : npm install sharp --save-dev

const STATIC_DIR = new URL('../static', import.meta.url).pathname;
const SRC_DIR = new URL('../src', import.meta.url).pathname;
const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif'];

async function findImages(dir) {
    let results = [];
    const files = await readdir(dir);

    for (const file of files) {
        const filePath = join(dir, file);
        const fileStat = await stat(filePath);

        if (fileStat.isDirectory()) {
            const nestedResults = await findImages(filePath);
            results = [...results, ...nestedResults];
        } else if (IMAGE_EXTENSIONS.includes(extname(file).toLowerCase())) {
            results.push(filePath);
        }
    }

    return results;
}

async function optimizeImages() {
    try {
        console.log('🔍 Recherche des images...');

        // Recherche dans static et src
        const staticImages = await findImages(STATIC_DIR);
        const srcImages = await findImages(SRC_DIR);
        const allImages = [...staticImages, ...srcImages];

        if (allImages.length === 0) {
            console.log('✅ Aucune image trouvée à optimiser.');
            return;
        }

        console.log(`🖼️ ${allImages.length} images trouvées.`);

        // Installation de sharp si pas déjà fait
        try {
            console.log('📦 Vérification des dépendances...');
            execSync('npm list sharp || npm install sharp --save-dev');
        } catch (error) {
            console.error('❌ Erreur lors de l\'installation des dépendances:', error);
            return;
        }

        // Optimisation des images avec sharp (ajouté dynamiquement)
        const sharp = await import('sharp');

        console.log('🔄 Début de l\'optimisation...');

        for (const imagePath of allImages) {
            const webpPath = imagePath.replace(/\.(png|jpg|jpeg|gif)$/i, '.webp');

            try {
                await sharp.default(imagePath)
                    .webp({ quality: 80 })
                    .toFile(webpPath);

                console.log(`✅ Optimisé: ${imagePath} → ${webpPath}`);
            } catch (error) {
                console.error(`❌ Erreur lors de l'optimisation de ${imagePath}:`, error);
            }
        }

        console.log('🎉 Optimisation terminée !');

    } catch (error) {
        console.error('❌ Erreur lors de l\'optimisation des images:', error);
    }
}

optimizeImages();
