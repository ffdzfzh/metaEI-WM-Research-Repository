function code_book = GS()

set(0,'defaultAxesFontSize', 10);
script_dir = fileparts(mfilename('fullpath'));

num_x = 48;
num_y = 32;

p = 20e-3;
c = 3*10^8;
f0 = 3.5*10^9;


lambda = c/f0;
k = 2*pi/lambda;
% load('horn_data.mat')
iterative = 200;

%%
obs_num_theta = 90; 
obs_num_phi = 90;

theta_vec = linspace(-90, 90, obs_num_theta);
phi_vec = linspace(-90, 90, obs_num_phi);
[Theta_grid, Phi_grid] = meshgrid(theta_vec, phi_vec);

known_abs_spatial = zeros(obs_num_theta, obs_num_phi);

target_theta = 45;
target_phi = -10;
% 
[~, idx_theta] = min(abs(theta_vec - target_theta));
[~, idx_phi] = min(abs(phi_vec - target_phi));

known_abs_spatial(idx_phi, idx_theta) = 1; 
known_abs_spatial(idx_phi-1:idx_phi+1, idx_theta-1:idx_theta+1) = 1; 

image_objamp_single = reshape(known_abs_spatial, [], 1);
image_objamp_single = image_objamp_single / sum(image_objamp_single);


% A = load("Initial_Source_20251126_1506.mat");
load(fullfile(script_dir, 'scan_data', 'normal_incidence_61p5cm.mat'));
freq_index = 8;  % 8-3.5GHz
% freq_index = 11;  % 11-5GHz
[ny, nx, nfreq] = size(Spara_matrix);
E = Spara_matrix(:, :, freq_index);
% E = cellfun(@(x) x(51,3),A.sData,'UniformOutput',false);
% E = cell2mat(E);
feed_source=E(2:4:128,2:4:128);
bound = zeros(32, 8);
feed_source = [bound feed_source bound];
horn_imamp_single = abs(feed_source);
horn_imamp_single = reshape(horn_imamp_single,[],1);
horn_impha_single = angle(feed_source);
horn_impha_single = reshape(horn_impha_single,[],1);
figure(1)
subplot(231)
array2imageshow(horn_imamp_single,num_x,num_y);title('antenna amp');
colorbar;
subplot(232)
array2imageshow(horn_impha_single/pi*180,num_x,num_y);title('antenna phase');
colorbar;

phase_estimate = ones(num_x*num_y,1);  
% phase_estimate=pi*rand(num_y*num_x,1); 

%%
[metrix,metrix_inv] = Creat_FarField_Metrix(num_x,num_y, p, lambda, Theta_grid, Phi_grid);

%%
zeta=zeros(iterative,1);
Eff =zeros(iterative,1);

Ws_temp = 1;
temp2 =1;
for pp = 1:iterative 
    signal_estimate_spatial = horn_imamp_single.*exp(1i*(phase_estimate));   
  
    target = metrix * signal_estimate_spatial;
    
    abs_temp1 = abs(target); 
    Ws = Ws_temp * sum(abs_temp1(:))./abs_temp1.*image_objamp_single/sum(image_objamp_single(:));
    Ws_temp = Ws;
    
    temp2 = metrix_inv * (Ws.*target./abs_temp1);
    phase_estimate = angle(temp2);                                      
 
   object_error=(abs_temp1./sum(abs_temp1(:))-image_objamp_single./sum(image_objamp_single(:))).^2;
   zeta(pp,1) = 100*sqrt(sum(object_error(:))/5041); 
   
   power_in = horn_imamp_single.*horn_imamp_single;
   power_out = abs_temp1.*abs_temp1;
   Eff(pp,1) =sum(power_out(:))/sum(power_in(:));
end  
	
subplot(233);
array2imageshow(phase_estimate/pi*180,num_x,num_y);title('Uncompensated optimized phase distribution'); 
colorbar;
% subplot(224);
% colorbar;

%%
zeta_gui = (zeta-min(zeta(:)))./max((zeta-min(zeta(:))))*100;
Eff_gui = Eff./max(Eff(:))*100;
figure('Color',[1 1 1]);
set(0,'defaultAxesFontSize', 30);
set(gca, 'LineWidth',1,'GridAlpha',0.6)
%title('Eff and RMSE')
%grid on;
yyaxis left;
plot(Eff_gui,'linewidth',3);
ylim([0,100]);
ylabel('efficiency(%)','FontSize',30);

yyaxis right;
plot(zeta_gui,'linewidth',3);
ylim([0,100]);
ylabel('RMSE(%)','FontSize',30);

%%
set(0,'defaultAxesFontSize', 10);

phase_last = (phase_estimate - horn_impha_single)/pi*180;

phase_last = phase_last+540;
phase_last = rem(phase_last,360);
% 


%% 

array_last=data2array(phase_last,num_x,num_y, 0);
array_last = mod(array_last,360);
[num_y,num_x]=size(array_last); 
array_last_quantification=zeros(num_y,num_x);
Sidelength=zeros(num_y,num_x);

for i=1:num_y
     for j=1:num_x
         if  array_last(i,j)>=0 && array_last(i,j)<180
             array_last_quantification(i,j) = 90;
             Sidelength(i,j) = 1;
         elseif array_last(i,j)>=180 && array_last(i,j)<360
             array_last_quantification(i,j) = 270;
             Sidelength(i,j) = 0;
         end
     end    
end
% for i=1:num_y
%      for j=1:num_x
%          code_book(i,j)=Sidelength(num_y+1-i,num_x+1-j);
%      end
% end
code_book = Sidelength;
% figure(1)
% subplot(2,3,6)
% array2imageshow(array_last_quantification,num_x,num_y);
% colorbar;
% colormap(jet); 
% 
% figure(527)
% colormap('turbo');

figure(1)
subplot(234);
array2imageshow(code_book,num_x,num_y);
title("coding");
colormap("parula");
colorbar;

subplot(235);
imagesc(theta_vec, phi_vec, known_abs_spatial);
title('Target Far-field Pattern');
xlabel('\theta (deg)'); ylabel('\phi (deg)');
colorbar; axis square;

final_pattern = reshape(abs(target), obs_num_phi, obs_num_theta);
subplot(236);
imagesc(theta_vec, phi_vec, final_pattern);
title('Optimized Far-field Pattern');
xlabel('\theta (deg)'); ylabel('\phi (deg)');
colorbar; axis square;

end



