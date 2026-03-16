import forge from 'node-forge';

export function encrypt(publicKey, value) {
  const encryptpublicKey = forge.pki.publicKeyFromPem(publicKey);
  const encrypted = encryptpublicKey.encrypt(forge.util.encodeUtf8(value), 'RSA-OAEP', {
    md: forge.md.sha256.create(),
    mgf1: {
      md: forge.md.sha256.create()
    }
  });
  const encryptedValue = forge.util.bytesToHex(encrypted)
  return encryptedValue
}

export function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/; // Basic email validation regex
  return emailRegex.test(email);
};

export function getCsrfToken() {
  const csrfCookie = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_access_token='));
  return csrfCookie ? csrfCookie.split('=')[1] : null;
}

export function loadNewTime(time, ogtable) {
  const table = JSON.parse(ogtable)
  const newTime = { "time": time }
  table.push(newTime)
  return JSON.stringify(table)
}

export function getAverageTime(ogtable) {
  const table = JSON.parse(ogtable)
  if (table.length === 0) {
    return 30000
  }
  const times = table.map(item => item.time);

  const averageTime = times.reduce((sum, time) => sum + time, 0) / times.length;
  const roundedNumber = Math.round(averageTime);
  return roundedNumber
}