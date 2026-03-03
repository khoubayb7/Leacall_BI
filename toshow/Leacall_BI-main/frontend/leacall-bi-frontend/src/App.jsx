
import { useState } from 'react'
import './App.css'
import LeacallBiLogin from './compos/LeacallBiLogin.jsx'
import ContactUs from './compos/ContactUs.jsx'

function App() {
  const [page, setPage] = useState('login')

  return (
    <>
      {page === 'login' ? (
        <LeacallBiLogin onContactClick={() => setPage('contact')} />
      ) : (
        <ContactUs onBackClick={() => setPage('login')} />
      )}
    </>
  )
}

export default App
