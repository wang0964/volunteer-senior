const API_BASE = 'https://localhost:5000';
const endpoint = '/api/register/senior';


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
    heroLead:'BuddyLink supports <strong>senior sign-up</strong> and <strong>volunteer sign-up</strong>. We match by interests and availability. Services include friendly chats, video companionship, reading mail, short walks, groceries/meds pickup, and basic tech help.',
    ctaSenior:"I'm a senior, need help", ctaVolunteer:"I'm a volunteer, want to help",
    registerTitle:'Registration',
    registerSub:'Choose your role to sign up. Fields are demo only (client-side validation). Hook up your backend at <code>/register/senior</code> and <code>/register/volunteer</code>.',
    tabSenior:'Senior Sign-up', tabVolunteer:'Volunteer Sign-up',
    name:'Name', namePh:'Enter full name', age:'Age', agePh:'e.g., 70', ageHelp:'Optional; helps us prioritize age-appropriate services.',
    phone:'Phone', phonePh:'e.g., 647-123-4567', email:'Email', emailPh:'example@email.com',
    city:'City / Area', cityPh:'e.g., Toronto / Scarborough', contactPref:'Preferred contact', optPhone:'Phone', optEmail:'Email', optVideo:'Video',
    needs:'Needed services (multi-select)', needChat:'Friendly chat', needVideo:'Video companionship', needRead:'Read letters/news', needWalk:'Short walk', needGrocery:'Groceries',needHealth:'Health' ,needTech:'Tech help',
    availability:'Availability', availabilityPh:'e.g., Mon/Wed/Fri 2–5 pm', prefLang:'Preferred language',
    notes:'Notes (health/accessibility)', notesPh:'Wheelchair access, allergies, etc.',
    submitSenior:'Submit senior sign-up', privacyAgree:'By submitting, you agree to our privacy terms.',
    sMsg:'Thanks! (demo) We will contact you soon for matching.',
    skills:'Services you can provide (multi-select)', background:'Background check', bgNo:'Not yet', bgProgress:'In progress', bgYes:'Completed',
    consent:'I agree to the volunteer code of conduct and privacy.', submitVolunteer:'Submit volunteer sign-up', prefill:'Prefill demo', vMsg:"Thanks for signing up! (demo) We'll match you based on your time and skills.",
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
    loginSuccess: 'Login submitted (demo).',
    male: 'Male',
    female: 'Female',
    other: 'Other',
    english: 'English',
    french: 'French',
    language: 'Language',
    navProfile: 'Profile',
    navRegister: 'Register',
    btnrole_senior: "I’m a senior, need help",
    btnvolunteer_senior: "I’m a volunteer, want to help",
    signup_senior: "Senior Sign-up",
    signup_volunteer: "Volunteer Sign-up",
    backtohome: "← Back to Home",
    introdution: "BuddyLink supports <strong>senior sign-up</strong> and <strong>volunteer sign-up</strong>We match by interests and availability. Services include friendly chats, video companionship, reading mail, groceries pickup and health consulation, and basic tech help.",
    introdution_title: "Connect volunteers with seniors for warm companionship and daily help",
    upcoming_event: "Upcoming Event",
  },
  fr: {
    navRegister:'Inscription', navAbout:'À propos', joinNow:"S'inscrire maintenant",
    heroTitle:"Relier des bénévoles aux aînés pour une compagnie chaleureuse et une aide au quotidien",
    heroLead:"BuddyLink prend en charge <strong>l'inscription des aînés</strong> et <strong>l'inscription des bénévoles</strong>. Nous faisons l'appariement selon les intérêts et les disponibilités. Services : conversation amicale, accompagnement vidéo, lecture du courrier, petites promenades, achats d'épicerie/médicaments, et aide technologique de base.",
    ctaSenior:"Je suis un aîné, j'ai besoin d'aide", ctaVolunteer:"Je suis bénévole, je veux aider",
    registerTitle:'Inscription',
    registerSub:"Choisissez votre rôle pour vous inscrire. Les champs sont en démonstration (validation côté client). Reliez votre serveur à <code>/register/senior</code> et <code>/register/volunteer</code>.",
    tabSenior:'Inscription aîné', tabVolunteer:'Inscription bénévole',
    name:'Nom', namePh:'Nom complet', age:'Âge', agePh:'ex. 70', ageHelp:"Optionnel ; nous aide à prioriser des services adaptés à l'âge.",
    phone:'Téléphone', phonePh:'ex. 647-123-4567', email:'Courriel', emailPh:'exemple@courriel.com',
    city:'Ville / Quartier', cityPh:'ex. Toronto / Scarborough', contactPref:'Contact préféré', optPhone:'Téléphone', optEmail:'Courriel', optVideo:'Vidéo',
    needs:'Services nécessaires (multi-sélection)', needChat:'Conversation amicale', needVideo:'Accompagnement vidéo', needRead:'Lire lettres/journaux', needWalk:'Petite marche', needGrocery:'Épicerie',needHealth:'Santé', needTech:'Aide techno',
    availability:'Disponibilités', availabilityPh:'ex. Lun/Me/Ven 14 h–17 h', prefLang:'Langue préférée',
    notes:'Notes (santé/accessibilité)', notesPh:"Accès fauteuil roulant, allergies, etc.",
    submitSenior:"Envoyer l'inscription aîné", privacyAgree:'En envoyant, vous acceptez nos conditions de confidentialité.',
    sMsg:"Merci ! (démo) Nous vous contacterons bientôt pour l'appariement.",
    skills:'Services que vous pouvez offrir (multi-sélection)', background:'Vérification d’antécédents', bgNo:'Pas encore', bgProgress:'En cours', bgYes:'Terminée',
    consent:"J'accepte le code de conduite des bénévoles et la confidentialité.", submitVolunteer:"Envoyer l'inscription bénévole", prefill:'Préremplir (démo)', vMsg:"Merci pour votre inscription ! (démo) Nous vous apparierons selon votre temps et vos compétences.",
    aboutTitle:'À propos de BuddyLink', aboutLead:"Page de démonstration au style organisme à but non lucratif moderne. Intégrez-la à votre projet et reliez les formulaires à votre serveur (Node/Flask/Spring, etc.).",
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
    loginSuccess: "Connexion envoyée (démo).",
    male: 'Homme',
    female: 'Femme',
    other: 'Autre',
    english: 'Anglais',
    french: 'Français',
    language: 'Langage',
    navProfile: 'Profil',
    navRegister: "S'inscrire",
    btnrole_senior: "Aîné·e, besoin d’aide",
    btnvolunteer_senior: "Bénévole, je veux aider",
    signup_senior: "Inscription des aînés",
    signup_volunteer: "Inscription des bénévoles",
    backtohome: "← Retour à l’accueil",
    introdution: "BuddyLink propose l’<strong>inscription des aînés</strong> et l’<strong>inscription des bénévoles</strong>. Nous jumelons selon les intérêts et les disponibilités. Les services comprennent des conversations amicales, de l’accompagnement vidéo, l’aide à la lecture du courrier, la cueillette d’épicerie, des conseils santé et un soutien technique de base.",
    introdution_title: "Relier des bénévoles et des aînés pour une compagnie chaleureuse et une aide quotidienne",
    upcoming_event: "Événement à venir",
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
// handleSubmit('form-senior','s-msg');
// handleSubmit('form-vol','v-msg');


// deep link to a specific tab
if (location.hash === '#volunteer') activate('vol');
if (location.hash === '#senior') activate('senior');

// ---- Login form handler ----

const loginForm = document.getElementById('loginForm');
if (loginForm) {
  const submitBtn = loginForm.querySelector('button[type="submit"]');
  const errorBox = document.getElementById('loginError');

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    

    const lang = document.documentElement.lang || 'en';
    const dict = (window.i18n && i18n[lang]) ? i18n[lang] : (i18n?.en || {});
    const text = (k, fallback) => dict[k] || fallback || k;


    if (!loginForm.reportValidity()) return;

    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
      (errorBox ? errorBox.textContent = text('loginMissing','Email and password are required.') : alert(text('loginMissing','Email and password are required.')));
      return;
    }


    const prevLabel = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = text('loggingIn', 'Logging in…');


    if (errorBox) errorBox.textContent = '';

    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ email, password }),
        credentials: 'include' 
      });


      let data = null;
      const textBody = await res.text();
      try { data = JSON.parse(textBody); } catch {  }
      console.log("[Login Response]", textBody);

      if (!res.ok || (data && data.success === false)) {
        // console.log("message", data.message);
        throw new Error(data.message || 'Submit failed');
        
      }


      if (data.data) {
           localStorage.setItem('email', data.data.email);
           localStorage.setItem('role', data.data.role);
      }

      // const redirectTo = new URLSearchParams(location.search).get('next') || '/';
      // location.assign(redirectTo);

      await showMsg({ title: 'Login', text: 'Success to login', icon: 'success' });

      const params = new URLSearchParams(location.search);
      const next   = params.get('next');
      const safeNext = (next && /^\/[^\s]*$/.test(next)) ? next : null;
      const target = safeNext || '/vs/index.html';   
      location.assign(target);


    } catch (err) {
      // (errorBox ? errorBox.textContent = err.message : alert(err.message));
      
      await showMsg({ title: 'Login', text: err.message, icon: 'error' });
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = prevLabel;
    }
  });
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////

function refreshAuthUI() {
  const btn = document.getElementById('ctaJoin');
  const regLink = document.getElementById('register-nav');
  const email = localStorage.getItem('email');         
  const role  = localStorage.getItem('role');
  const isLoggedIn = !!email;

  if (regLink) {
    if (isLoggedIn) {
      regLink.textContent = 'Profile';
      regLink.setAttribute('data-i18n', 'navProfile'); 
      const profileHref =
        role === 'volunteer' ? '/vs/volunteer-profile.html' :
        role === 'senior'    ? '/vs/senior-profile.html' :
                               '#';
      regLink.href = profileHref;
      console.log(role)
    } else {

      regLink.textContent = 'Register';
      regLink.setAttribute('data-i18n', 'navRegister');
      regLink.href = '/vs/pages/register.html'; 
    }
  }

  if (!btn) return;

  if (isLoggedIn) {
    btn.href = '#';
    btn.innerHTML = '<i class="fas fa-sign-out-alt"></i><span>Logout</span>';

    btn.replaceWith(btn.cloneNode(true));
    const freshBtn = document.getElementById('ctaJoin');
    freshBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {

        await fetch('/api/logout', { method: 'POST', credentials: 'include' }).catch(()=>{});
      } finally {
        localStorage.removeItem('email');
        localStorage.removeItem('role');
        refreshAuthUI();

        location.assign('/vs/index.html');
      }
    });
  } else {

    btn.href = '/vs/pages/login.html';
    btn.innerHTML = '<i class="fas fa-hands-helping"></i><span>Login</span>';

    btn.replaceWith(btn.cloneNode(true));
  }
}


document.addEventListener('DOMContentLoaded', refreshAuthUI);


/////////////////////////////////////////////////////////////////////////////////////////////////////////////


function showMsg({ title = 'Notice', text = '', icon = 'info', confirmText = 'OK' } = {}) {
  if (window.Swal && typeof Swal.fire === 'function') {
    return Swal.fire({
      title, text, icon, confirmButtonText: confirmText,
      customClass: { title: 'swal2-title-lg', htmlContainer: 'swal2-text-lg', confirmButton: 'swal2-btn-lg' }
    });
  }
  alert(title + (text ? '\n\n' + text : ''));
}



async function handleSubmitToApi(formId, msgId, endpoint, buildPayload){
  const form = document.getElementById(formId);
  const msg = document.getElementById(msgId);
  if (!form) return;

  // if (msg) msg.hidden = true;

  form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const lang = document.documentElement.lang || 'en';
    const dict = i18n[lang] || i18n.en;

    const payload = buildPayload(form);

    // if (payload.__invalid) {
    //   alert(dict.requiredAlert);
    //   return;
    // }
    console.log(payload);
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || 'Submit failed');

      // msg.hidden = false;
      form.reset();
      form.querySelector('input,select,textarea')?.focus();
      await showMsg({title: 'Registration',text:  'Thank you! We will contact you soon.',icon:  'success', confirmText: 'OK' });
    } catch (err) {
      await showMsg({ title: 'Registration', text: err?.message || 'Failed to register', icon: 'error' });
      // alert(err.message);
    }
  });
}

// Senior register -> /api/register/senior
handleSubmitToApi('form-senior','s-msg','/api/register/senior', (form) => {
  return {
    firstname: form.querySelector('#s-fname').value.trim(),
    lastname: form.querySelector('#s-lname').value.trim(),
    age: form.querySelector('#s-age').value || null,
    phone: form.querySelector('#s-phone').value.trim(),
    email: form.querySelector('#s-email').value.trim(),
    city: form.querySelector('#s-city').value.trim(),
    address: form.querySelector('#s-address').value.trim(),
    contactPref: form.querySelector('#s-contact').value,
    language: form.querySelector('#s-language').value,
    notes: form.querySelector('#s-notes').value.trim(),
    password: form.querySelector('#s-password').value.trim(),
    re_password: form.querySelector('#s-re-password').value.trim(),
    // __invalid: !(form.querySelector('#s-fname').value && form.querySelector('#s-lname').value && form.querySelector('#s-phone').value)
  };
});


// Volunteer register -> /api/register/volunteer
// handleSubmitToApi('form-vol', 'v-msg', '/api/register/volunteer', (form) => {
//    return {
//   };
// });

handleSubmitToApi('form-vol', 'v-msg', '/api/register/volunteer', (form) => {
  const availability = Array.from(
    form.querySelectorAll('#scheduleTable input[type="checkbox"]:checked')
  ).map(cb => cb.name); // e.g., ["mon-morning","tue-evening"]

  const skills = Array.from(
    form.querySelectorAll('.checks input[type="checkbox"][name^="skill-"]:checked')
  ).map(cb => cb.value);

  const language = Array.from(
    form.querySelectorAll('.checks input[type="checkbox"][name^="lang-"]:checked')
  ).map(cb => cb.value);

  return {
    firstname: form.querySelector('#v-fname').value.trim(),
    lastname:  form.querySelector('#v-lname').value.trim(),
    email:     form.querySelector('#v-email').value.trim(),
    phone:     form.querySelector('#v-phone').value.trim(),
    city:      form.querySelector('#v-city').value.trim(),
    address:   form.querySelector('#v-address').value.trim(),
    gender:    form.querySelector('#v-gender').value.trim(),
    background: form.querySelector('#v-id').value, // 'no' | 'inprogress' | 'yes'
    skills, // ['chat','read',...]
    availability,            // Array of names
    password: form.querySelector('#v-password').value.trim(),
    re_password: form.querySelector('#v-re-password').value.trim(),
    gender: form.querySelector('#v-gender').value.trim(),
    language
    // consent: !!form.querySelector('input[name="consent"]')?.checked,
  };
});
