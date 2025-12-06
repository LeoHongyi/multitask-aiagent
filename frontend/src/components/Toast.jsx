import './Toast.css'

function Toast({ show, message, type }) {
  return (
    <div className={`toast ${show ? 'show' : ''} ${type}`}>
      {message}
    </div>
  )
}

export default Toast

