require 'spec_helper'

describe 'Consul with TLS enabled' do
  
  describe file('/opt/consul/cert') do
    it { should be_directory }
    it { should be_owned_by('consul') }
  end

  %w(ca.crt consul.crt consul.key).each do |file|
    describe file("/opt/consul/cert/#{file}") do
      it { should be_file }
      it { should be_owned_by('consul') }
    end
  end

  describe file('/opt/consul/cert/consul.crt') do
    its(:content) { should match /-----BEGIN CERTIFICATE-----.*-----END CERTIFICATE-----/m }
  end

  describe file('/opt/consul/cert/consul.key') do
    its(:content) { should match /-----BEGIN RSA PRIVATE KEY-----.*-----END RSA PRIVATE KEY-----/m }
  end

  describe file('/opt/consul/cert/ca.crt') do
    its(:content) { should match /-----BEGIN CERTIFICATE-----.*-----END CERTIFICATE-----/m }
  end

  describe file('/etc/consul.conf') do
    it { should be_file }
    its(:content) { should match /"ca_file": \"\/opt\/consul\/cert\/ca.crt\"/ }
    its(:content) { should match /"cert_file": \"\/opt\/consul\/cert\/consul.crt\"/ }
    its(:content) { should match /"key_file": \"\/opt\/consul\/cert\/consul.key\"/ }
    its(:content) { should match /"verify_incoming": true,/ }
    its(:content) { should match /"verify_outgoing": true,/ }
  end

  describe service('consul') do
    it { should be_enabled }
    it { should be_running }
  end
end