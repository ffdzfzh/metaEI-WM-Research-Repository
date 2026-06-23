function metacode = focus_ASK(x,y,z)
f = 3.5e9;
c = 3e8;
lambda = c / f; 
dx = 0.02; 
Nx = 48; Ny = 32; 
target1 = [x,y,z];
target2 = [0.81, 0.648, 3];
target3 = [0.81 , -0.648, 3];

A=load("Initial_Source_20251126_1506.mat");
% A=load("Initial_Source_20251126_1743.mat");
for i=51
E = cellfun(@(x) x(i,3),A.sData,'UniformOutput',false);
E=cell2mat(E);
Emax=max(max(abs(E)));
end
feed_source=E(2:2:64,2:2:64);
horn_imamp_single = abs(feed_source);
horn_impha_single = angle(feed_source);
source_phase = horn_impha_single;

x_coords = dx * ((0:Nx-1) - (Nx-1)/2); 
y_coords = dx * ((0:Ny-1) - (Ny-1)/2); 
[X, Y] = meshgrid(x_coords, y_coords);

Rn1 = sqrt( (X - target1(1)).^2 + (Y - target1(2)).^2 + target1(3)^2 );
Rn2 = sqrt( (X - target2(1)).^2 + (Y - target2(2)).^2 + target2(3)^2 );
Rn3 = sqrt( (X - target3(1)).^2 + (Y - target3(2)).^2 + target3(3)^2 );

k = 2*pi/lambda;
phase1 = -k * Rn1 + source_phase; 
phase2 = -k * Rn2 + source_phase;
phase3 = -k * Rn3 + source_phase;
ideal_phase = angle(1*exp(1i*phase1) + 0*exp(1i*phase2) + 0*exp(1i*phase3));

quantized_phase = zeros(Ny, Nx);
for i = 1:Ny
    for j = 1:Nx
        if ideal_phase(i,j) < pi/2 && ideal_phase(i,j) > -pi/2
            quantized_phase(i,j) = 0;
        else
            quantized_phase(i,j) = 1;
        end
    end
end

metacode = quantized_phase;
end

