import { useState } from 'react'
import { useMembers } from '@/hooks/useMembers'

export default function Members() {
  const members = useMembers()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('member')

  return (
    <div className="page">
      <div>
        <h1>Members</h1>
        <p className="muted">Invite people and manage workspace roles.</p>
      </div>

      <div className="grid two">
        <section className="card stack">
          <h2>Invite member</h2>
          <p className="muted">Invited users finish activation from the signup page with the same email.</p>
          <input className="input" value={email} onChange={e => setEmail(e.target.value)} placeholder="member@example.com" />
          <select className="select" value={role} onChange={e => setRole(e.target.value)}>
            <option value="admin">Admin</option>
            <option value="member">Member</option>
            <option value="viewer">Viewer</option>
          </select>
          <button className="button" onClick={() => members.invite.mutate({ email, role })} disabled={!email}>
            Send invite
          </button>
        </section>

        <section className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {members.members.map(member => (
                <tr key={member.id}>
                  <td>{member.name || 'Pending'}</td>
                  <td>{member.email}</td>
                  <td>
                    <select
                      className="select"
                      value={member.role}
                      onChange={e => members.updateRole.mutate({ memberId: member.id, role: e.target.value })}
                    >
                      <option value="admin">Admin</option>
                      <option value="member">Member</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </td>
                  <td>
                    <button className="button secondary" onClick={() => members.remove.mutate(member.id)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  )
}
