Vagrant.configure('2') do |config|

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = 'ubuntu/trusty64'

  config.ssh.forward_agent = true
  config.vm.synced_folder './', '/vagrant'

  config.vm.network :private_network, ip: "192.168.33.99"

  config.vm.provider :virtualbox do |vb|
    vb.customize ['modifyvm', :id, '--memory', '1024']
    vb.customize ['modifyvm', :id, '--ioapic', 'on']
  end

end
