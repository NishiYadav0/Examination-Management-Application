<template>
  <footer class="emp-footer">
    <div class="container">
      <div class="row g-4">
        <div class="col-lg-4">
          <AppLogo light />
          <p class="mt-3 opacity-75 small pe-lg-5">A modern examination management portal to schedule vivas, practicals and project demos,
            book slots and publish rubric based results — all in one place.</p>
          <div class="d-flex gap-2">
            <a class="footer-social" href="https://github.com" target="_blank" rel="noopener" aria-label="GitHub"><i class="bi bi-github"></i></a>
            <a class="footer-social" href="https://linkedin.com" target="_blank" rel="noopener" aria-label="LinkedIn"><i class="bi bi-linkedin"></i></a>
            <a class="footer-social" href="https://youtube.com" target="_blank" rel="noopener" aria-label="YouTube"><i class="bi bi-youtube"></i></a>
          </div>
        </div>
        <div class="col-6 col-lg-2">
          <h6>Platform</h6>
          <ul>
            <li><router-link to="/">Home</router-link></li>
            <li><router-link :to="{ path: '/', hash: '#features' }">Features</router-link></li>
            <li><router-link to="/about">About</router-link></li>
            <li><router-link to="/contact">Contact</router-link></li>
          </ul>
        </div>
        <div class="col-6 col-lg-2">
          <h6>Account</h6>
          <ul>
            <li><router-link to="/login">Log in</router-link></li>
            <li><router-link to="/register">Student sign-up</router-link></li>
            <li><router-link to="/support">Help & Support</router-link></li>
            <li><router-link to="/profile">My profile</router-link></li>
          </ul>
        </div>
        <div class="col-lg-4">
          <h6>Get in touch</h6>
          <ul class="list-unstyled small">
            <li class="mb-2"><i class="bi bi-geo-alt me-2"></i>IIT Madras, Chennai – 600036</li>
            <li class="mb-2"><i class="bi bi-envelope me-2"></i>support@emp.local</li>
            <li class="mb-2"><i class="bi bi-telephone me-2"></i>+91 44 2257 0000</li>
            <li><i class="bi bi-clock me-2"></i>Mon – Fri · 9:00 AM – 6:00 PM</li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom d-flex flex-column flex-md-row justify-content-between gap-2">
        <span>© {{ year }} Examination Management Portal. Built with Flask · Vue · Bootstrap.</span>
        <span>Made for MAD-II · IIT Madras BS</span>
      </div>
    </div>
  </footer>
</template>
<script>
import AppLogo from './AppLogo.vue'
export default { name: 'PublicFooter', components: { AppLogo }, data: () => ({ year: new Date().getFullYear() }) }
</script>
<style>
.emp-footer { background: #0f172a; color: #cbd5e1; padding: 4rem 0 1.5rem; margin-top: 4rem; }
.emp-footer h6 { color: #fff; font-weight: 700; margin-bottom: 1rem; }
.emp-footer ul { list-style: none; padding: 0; }
.emp-footer ul li { margin-bottom: .55rem; }
.emp-footer a { color: #94a3b8; text-decoration: none; transition: color .15s; }
.emp-footer a:hover { color: #fff; }
.footer-social { width: 38px; height: 38px; border-radius: 10px; background: rgba(255,255,255,.07); display: inline-flex; align-items: center; justify-content: center; }
.footer-social:hover { background: var(--emp-primary); }
.footer-bottom { border-top: 1px solid rgba(255,255,255,.08); margin-top: 2.5rem; padding-top: 1.25rem; font-size: .82rem; color: #64748b; }
</style>
