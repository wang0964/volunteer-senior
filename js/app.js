// const API_BASE = 'https://localhost:5000';
// const endpoint = '/api/register/senior';
import { i18n } from './language-string.js';
// console.log('i18n loaded:', i18n); 

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


function toYMD(date = new Date()) {
  const d = date instanceof Date ? date : new Date(date);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}/${m}/${day}`;
}

function getNextWeekRange(baseDate = new Date()) {
  const today = new Date(baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate());

  const dow = today.getDay();
  const daysUntilNextMonday = ((8 - dow) % 7) || 7; 

  const start_d = new Date(today);
  start_d.setDate(today.getDate() + daysUntilNextMonday);
  start_d.setHours(0, 0, 0, 0); 

  const end_d = new Date(start_d);
  end_d.setDate(start_d.getDate() + 6);
  end_d.setHours(23, 59, 59, 999); 

  return {start_d, end_d};
}



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
// handleSubmit('form-ask','a-msg');

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
      // console.log("[Login Response]", textBody);

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

      // let lan = localStorage.getItem('lang') || 'en';
      if (lang=='en'){
        await showMsg({ title: 'Login', text: 'Success to login', icon: 'success' });
      } else {
        await showMsg({ title: 'Connexion', text: 'Connexion réussie', icon: 'success' });
      }

      const params = new URLSearchParams(location.search);
      const next   = params.get('next');
      const safeNext = (next && /^\/[^\s]*$/.test(next)) ? next : null;
      const target = safeNext || '/vs/index.html';   
      if (data.data.role=='senior'){
        // document.getElementById('forservice').style.removeProperty('display');
        location.assign('/vs/pages/askforservice.html');
        
      } 
      else if (data.data.role=='volunteer'){

        location.assign('/vs/pages/volunteer-dashboard.html');
        
      } 
      else {
        // document.getElementById('forservice').style.display = 'none';
        location.assign(target);
        
      }
    } catch (err) {
      // let lan2 = localStorage.getItem('lang') || 'en';
      // console.log(lan2);
      if (lang=='en') {
        await showMsg({ title: 'Login', text: err?.message || 'Fail to login', icon: 'error' });
      } else {
        if (err?.message=='Email and password are required'){
          e_msg='L’adresse courriel et le mot de passe sont requis';
        } else if (err?.message=='Invalid email or password') {
          e_msg='Adresse courriel ou mot de passe incorrect';
        } else {
          e_msg='Échec de l’ouverture de session';
        }
        await showMsg({ title: 'Connexion', text: e_msg, icon: 'error' });
      }
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



  const {start_d: s, end_d: e}=getNextWeekRange();
  document.getElementById('s-date').textContent = toYMD(s);
  document.getElementById('e-date').textContent = toYMD(e);

  if (regLink) {
    if (isLoggedIn) {
      regLink.textContent = 'Profile';
      regLink.setAttribute('data-i18n', 'navProfile'); 
      const profileHref =
        role === 'volunteer' ? '/vs/volunteer-profile.html' :
        role === 'senior'    ? '/vs/senior-profile.html' :
                               '#';
      regLink.href = profileHref;
      // console.log(role)
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


    if (role=='senior'){
      document.getElementById('forservice').style.removeProperty('display');
      document.getElementById('senior_btn').setAttribute('href', 'pages/askforservice.html');
      document.getElementById('volunteer_btn').setAttribute('href', 'pages/login.html');

      document.getElementById('senior_btn').style.removeProperty('display');
      document.getElementById('volunteer_btn').style.display = 'none';

    } else {
      document.getElementById('forservice').style.display = 'none';
      document.getElementById('senior_btn').setAttribute('href', 'pages/login.html');
      document.getElementById('volunteer_btn').setAttribute('href', 'pages/login.html');

      document.getElementById('volunteer_btn').style.removeProperty('display');
      document.getElementById('senior_btn').style.display = 'none';
    }    

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

      document.getElementById('forservice').style.display = 'none';

      document.getElementById('senior_btn').setAttribute('href', 'pages/login.html');
      document.getElementById('volunteer_btn').setAttribute('href', 'pages/login.html');

      document.getElementById('volunteer_btn').style.removeProperty('display');
      document.getElementById('senior_btn').style.removeProperty('display');



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
      // let lan3 = localStorage.getItem('lang') || 'en';

      if (formId=='form-senior' || formId=='form-vol'){
        if (lang=='en'){
          await showMsg({title: 'Registration',text:  'Thank you! We will contact you soon.',icon:  'success', confirmText: 'OK' });
        } else {
          await showMsg({title: 'Inscription',text:  'Merci ! Nous vous contacterons sous peu.',icon:  'success', confirmText: 'OK' });
        }
      } else if (formId=='form-ask'){
        if (lang=='en'){
          await showMsg({title: 'Application',text:  'Thank you! We will contact you soon.',icon:  'success', confirmText: 'OK' });
        } else {
          await showMsg({title: 'Candidature',text:  'Merci ! Nous vous contacterons sous peu.',icon:  'success', confirmText: 'OK' });
        }
      }
    } catch (err) {
      // let lan4 = localStorage.getItem('lang') || 'en';
      if (formId=='form-senior' || formId=='form-vol'){
        if (lang=='en'){
          await showMsg({ title: 'Registration', text: err?.message || 'Failed to register', icon: 'error' });
        } else {
          err_msg=err?.message;
          if (err_msg=='Email and password are required'){
            err_msg='L’adresse courriel et le mot de passe sont requis';
          } else if (err_msg=='Passwords do not match'){
            err_msg='Les mots de passe ne concordent pas';
          } else if (err_msg=='Password must have 8 letters at least'){
            err_msg='Le mot de passe doit contenir au moins 8 caractères';
          } else if (err_msg=='Age must be a number'){
            err_msg='L’âge doit être un nombre';
          } else if (err_msg=='Email already registered'){
            err_msg='Cette adresse courriel est déjà utilisée';
          } else {
            err_msg='L’inscription a échoué';
          }
          await showMsg({ title: 'Inscription', text: err_msg, icon: 'error' });
        }
        // alert(err.message);
      }
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
    language,
    self_description: form.querySelector('#v-self-description').value.trim(),
    // consent: !!form.querySelector('input[name="consent"]')?.checked,
  };
});


handleSubmitToApi('form-ask', 'a-msg', '/api/askfor', (form) => {
  const appointment = Array.from(
    form.querySelectorAll('#scheduleTable input[type="checkbox"]:checked')
  ).map(cb => cb.name); // e.g., ["mon-morning","tue-evening"]

  const askfor = Array.from(
    form.querySelectorAll('.checks input[type="checkbox"][name^="need-"]:checked')
  ).map(cb => cb.value);

  const email = localStorage.getItem('email'); 

  return {
    email,
    appointment,
    askfor,
    additional_requirement: form.querySelector('#ask-notes').value.trim(),
    // consent: !!form.querySelector('input[name="consent"]')?.checked,
  };
});

