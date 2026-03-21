export const generateProjectCover = (name) => {
  const canvas = document.createElement('canvas');
  canvas.width = 720;
  canvas.height = 400;
  const ctx = canvas.getContext('2d');

  // djb2 hash
  let h = 5381;
  for (let i = 0; i < name.length; i++) {
    h = ((h << 5) + h) ^ name.charCodeAt(i);
  }
  const hash = Math.abs(h);

  // Palettes: warm ivory/brown/gold tones
  const palettes = [
    ['#faf7f0', '#f2ede0', '#e5dfcc'],
    ['#f5f0e1', '#ede4d1', '#dfd3b6'],
    ['#fcfaf5', '#f7f2e8', '#ede4d1'],
    ['#fdfcf0', '#f9f7d9', '#f2efb6'],
    ['#f8f5ec', '#f1ebd5', '#e4daba']
  ];
  const palette = palettes[hash % palettes.length];
  
  // Background
  ctx.fillStyle = palette[0];
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Pattern
  const patternType = hash % 4;
  ctx.strokeStyle = palette[2];
  ctx.fillStyle = palette[1];
  ctx.lineWidth = 2;

  if (patternType === 0) { // Concentric Circles
    for (let i = 0; i < 6; i++) {
      ctx.beginPath();
      ctx.arc(canvas.width / 2, canvas.height / 2, (i + 1) * 30 + (hash % 20), 0, Math.PI * 2);
      ctx.stroke();
    }
  } else if (patternType === 1) { // Grid Lines
    const step = 40;
    for (let x = 0; x < canvas.width; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }
  } else if (patternType === 2) { // Diagonal Stripes
    for (let i = -canvas.width; i < canvas.width; i += 40) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i + 400, canvas.height); ctx.stroke();
    }
  } else { // Floating Rectangles
    for (let i = 0; i < 8; i++) {
      const x = ((hash + i * 137) % (canvas.width - 100));
      const y = ((hash + i * 223) % (canvas.height - 100));
      ctx.strokeRect(x, y, 80, 80);
    }
  }

  // Dark footer bar
  ctx.fillStyle = '#1a1510';
  ctx.fillRect(0, canvas.height - 60, canvas.width, 60);
  
  // Repo name text
  ctx.fillStyle = '#faf7f0';
  ctx.font = 'bold 18px DM Mono';
  ctx.textAlign = 'center';
  ctx.letterSpacing = '4px';
  ctx.fillText(name.toUpperCase(), canvas.width / 2, canvas.height - 25);

  return canvas.toDataURL('image/png');
};
