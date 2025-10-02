// ---- Tabs (guarded so pages without tabs won't throw) ----
const tabSenior = document.getElementById('tab-senior');
const tabVol = document.getElementById('tab-vol');
const panelSenior = document.getElementById('panel-senior');
const panelVol = document.getElementById('panel-vol');

function activate(which){
  const isSenior = which === 'senior';
  tabSenior?.setAttribute('aria-selected', isSenior);
  tabVol?.setAttribute('aria-selected', !isSenior);
  panelSenior?.classList.toggle('active', isSenior);
  panelVol?.classList.toggle('active', !isSenior);
  (isSenior ? panelSenior : panelVol)?.querySelector('input,select,textarea')?.focus({ preventScroll: true });
}

if (tabSenior && tabVol && panelSenior && panelVol) {
  tabSenior.addEventListener('click', () => activate('senior'));
  tabVol.addEventListener('click', () => activate('vol'));
}

// ---- i18n dictionaries ----
const i18n = {
  en: {
    navRegister:'Register', navAbout:'About', joinNow:'Join now',
    heroTitle:'Connect volunteers with seniors for warm companionship and daily help',
    heroLead:'BuddyLink supports <strong>senior sign‑up</strong> and <strong>volunteer sign‑up</strong>. We match by interests and availability. Services include friendly chats, video companionship, reading mail, short walks, groceries/meds pickup, and basic tech help.',
    ctaSenior:"I'm a senior, need help", ctaVolunteer:"I'm a volunteer, want to help",
    registerTitle:'Registration', registerSub:'Choose your role to sign up. Fields are demo only (client‑side validation). Hook up your backend at <code>/api/register-senior</code> and <code>/api/register-volunteer</code>.',
    tabSenior:'Senior Sign‑up', tabVolunteer:'Volunteer Sign‑up',
    name:'Name', namePh:'Enter full name', age:'Age', agePh:'e.g., 70', ageHelp:'Optional; helps us prioritize age‑appropriate services.',
    phone:'Phone', phonePh:'e.g., 647-123-4567', email:'Email', emailPh:'example@email.com',
    city:'City / Area', cityPh:'e.g., Toronto / Scarborough', contactPref:'Preferred contact', optPhone:'Phone', optEmail:'Email', optVideo:'Video',
    needs:'Needed services (multi‑select)', needChat:'Friendly chat', needVideo:'Video companionship', needRead:'Read letters/news', needWalk:'Short walk', needGrocery:'Groceries/meds', needTech:'Tech help',
    availability:'Availability', availabilityPh:'e.g., Mon/Wed/Fri 2–5 pm', prefLang:'Preferred language',
    notes:'Notes (health/accessibility)', notesPh:'Wheelchair access, allergies, etc.',
    submitSenior:'Submit senior sign‑up', privacyAgree:'By submitting, you agree to our privacy terms.',
    sMsg:'Thanks! (demo) We will contact you soon for matching.',
    skills:'Services you can provide (multi‑select)', background:'Background check', bgNo:'Not yet', bgProgress:'In progress', bgYes:'Completed',
    consent:'I agree to the volunteer code of conduct and privacy.', submitVolunteer:'Submit volunteer sign‑up', prefill:'Prefill demo', vMsg:"Thanks for signing up! (demo) We'll match you based on your time and skills.",
    aboutTitle:'About BuddyLink', aboutLead:'This is a demo page in a modern nonprofit style. Integrate it into your project and connect both forms to your backend (Node/Flask/Spring, etc.).',
    about1:'Fully responsive layout', about2:'Accessibility: labels & ARIA', about3:'Basic client validation & messages', about4:'Extensible to auth/database',
    demoNote:'Demo only: submissions show a local success message',
    requiredAlert:'Please complete required fields / consent.',
    // Login page
    loginTitle: 'Login',
    loginWelcome: 'Welcome back! Please sign in to continue.',
    labelEmail: 'Email',
    phEmail: 'you@example.com',
    emailHint: 'Use the email you registered with.',
    labelPassword: 'Password',
    phPassword: 'Your password',
    rememberMe: 'Remember me',
    btnLogin: 'Login',
    noAccount: "Don't have an account?",
    goRegister: 'Register',
    navHome: 'Home',
    loginMissing: 'Please enter email and password.',
    loginSuccess: 'Login submitted (demo).'
  },
  fr: {
    navRegister:'Inscription', navAbout:'À propos', joinNow:"S'inscrire maintenant",
    heroTitle:"Relier des bénévoles aux aînés pour une compagnie chaleureuse et une aide au quotidien",
    heroLead:"BuddyLink prend en charge <strong>l'inscription des aînés</strong> et <strong>l'inscription des bénévoles</strong>. Nous faisons l'appariement selon les intérêts et les disponibilités. Services : conversation amicale, accompagnement vidéo, lecture du courrier, petites promenades, achats d'épicerie/médicaments, et aide technologique de base.",
    ctaSenior:"Je suis un aîné, j'ai besoin d'aide", ctaVolunteer:"Je suis bénévole, je veux aider",
    registerTitle:'Inscription', registerSub:"Choisissez votre rôle pour vous inscrire. Les champs sont en démonstration (validation côté client). Reliez votre serveur à <code>/api/register-senior</code> et <code>/api/register-volunteer</code>.",
    tabSenior:'Inscription aîné', tabVolunteer:'Inscription bénévole',
    name:'Nom', namePh:'Nom complet', age:'Âge', agePh:'ex. 70', ageHelp:"Optionnel ; nous aide à prioriser des services adaptés à l'âge.",
    phone:'Téléphone', phonePh:'ex. 647-123-4567', email:'Courriel', emailPh:'exemple@courriel.com',
    city:'Ville / Quartier', cityPh:'ex. Toronto / Scarborough', contactPref:'Contact préféré', optPhone:'Téléphone', optEmail:'Courriel', optVideo:'Vidéo',
    needs:'Services nécessaires (multi‑sélection)', needChat:'Conversation amicale', needVideo:'Accompagnement vidéo', needRead:'Lire lettres/journaux', needWalk:'Petite marche', needGrocery:'Épicerie/médicaments', needTech:'Aide techno',
    availability:'Disponibilités', availabilityPh:'ex. Lun/Me/Ven 14 h–17 h', prefLang:'Langue préférée',
    notes:'Notes (santé/accessibilité)', notesPh:"Accès fauteuil roulant, allergies, etc.",
    submitSenior:"Envoyer l'inscription aîné", privacyAgree:'En envoyant, vous acceptez nos conditions de confidentialité.',
    sMsg:"Merci ! (démo) Nous vous contacterons bientôt pour l'appariement.",
    skills:'Services que vous pouvez offrir (multi‑sélection)', background:'Vérification d’antécédents', bgNo:'Pas encore', bgProgress:'En cours', bgYes:'Terminée',
    consent:"J'accepte le code de conduite des bénévoles et la confidentialité.", submitVolunteer:"Envoyer l'inscription bénévole", prefill:'Préremplir (démo)', vMsg:"Merci pour votre inscription ! (démo) Nous vous apparierons selon votre temps et vos compétences.",
    aboutTitle:'À propos de BuddyLink', aboutLead:"Page de démonstration au style organisme à but non lucratif moderne. Intégrez‑la à votre projet et reliez les formulaires à votre serveur (Node/Flask/Spring, etc.).",
    about1:'Mise en page entièrement responsive', about2:'Accessibilité : libellés et ARIA', about3:'Validation et messages côté client', about4:"Extensible à l'authentification/base de données",
    demoNote:"Démonstration : l’envoi affiche un message local de réussite",
    requiredAlert:'Veuillez remplir les champs requis / consentement.',
    // Login page
    loginTitle: "Connexion",
    loginWelcome: "Heureux de vous revoir ! Veuillez vous connecter pour continuer.",
    labelEmail: "E-mail",
    phEmail: "vous@exemple.com",
    emailHint: "Utilisez l’e-mail avec lequel vous vous êtes inscrit.",
    labelPassword: "Mot de passe",
    phPassword: "Votre mot de passe",
    rememberMe: "Se souvenir de moi",
    btnLogin: "Connexion",
    noAccount: "Vous n’avez pas de compte ?",
    goRegister: "S’inscrire",
    navHome: "Accueil",
    loginMissing: "Veuillez saisir l’e-mail et le mot de passe.",
    loginSuccess: "Connexion envoyée (démo)."
  }
};

// ---- i18n apply ----
const langSelect = document.getElementById('langSelect');

function applyI18n(lang){
  const dict = i18n[lang] || i18n.en;
  document.documentElement.lang = lang;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key] !== undefined) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = dict[key];
      } else {
        el.innerHTML = dict[key];
      }
    }
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (dict[key] !== undefined) el.placeholder = dict[key];
  });

  localStorage.setItem('lang', lang);
  if (langSelect) langSelect.value = lang;
}

// init language
const savedLang = localStorage.getItem('lang') || 'en';
if (langSelect) langSelect.value = savedLang;
applyI18n(savedLang);
langSelect?.addEventListener('change', e => applyI18n(e.target.value));

// ---- Register page validators (safe on pages without those forms) ----
function handleSubmit(formId, msgId){
  const form = document.getElementById(formId);
  const msg = document.getElementById(msgId);
  if (!form) return;
  form.addEventListener('submit', (e)=>{
    e.preventDefault();
    const lang = document.documentElement.lang || 'en';
    const dict = i18n[lang] || i18n.en;
    const invalid = [...form.querySelectorAll('[required]')]
      .some(el => !el.value || (el.type === 'checkbox' && !el.checked && el.name === 'consent'));
    if (invalid) {
      alert(dict.requiredAlert);
      return;
    }
    if (msg) msg.hidden = false;
    form.reset();
    form.querySelector('input,select,textarea')?.focus();
  });
}
handleSubmit('form-senior','s-msg');
handleSubmit('form-vol','v-msg');

// prefill demo on register page
document.getElementById('prefill')?.addEventListener('click',()=>{
  const n = document.getElementById('v-name'); if (n) n.value='Alex Zhang';
  const e = document.getElementById('v-email'); if (e) e.value='alex@example.com';
  const p = document.getElementById('v-phone'); if (p) p.value='647-555-1212';
  const c = document.getElementById('v-city'); if (c) c.value='Toronto';
  const a = document.getElementById('v-availability'); if (a) a.value='Weekend mornings; weekday evenings';
  document.querySelector('input[name="skills"][value="chat"]')?.setAttribute('checked','checked');
  document.querySelector('input[name="skills"][value="walk"]')?.setAttribute('checked','checked');
});

// deep link to a specific tab
if (location.hash === '#volunteer') activate('vol');
if (location.hash === '#senior') activate('senior');

// ---- Login form handler (only if present) ----
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', function(e){
    e.preventDefault();
    const lang = document.documentElement.lang || 'en';
    const dict = i18n[lang] || i18n.en;
    const email = document.getElementById('loginEmail')?.value.trim();
    const pwd = document.getElementById('loginPassword')?.value;
    if (!email || !pwd) {
      alert(dict.loginMissing);
      return;
    }
    alert(dict.loginSuccess);
  });
}
