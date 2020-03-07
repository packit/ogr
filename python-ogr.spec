%global srcname ogr

Name:           python-%{srcname}
Version:        0.11.0
Release:        1%{?dist}
Summary:        One API for multiple git forges

License:        MIT
URL:            https://github.com/packit-service/ogr
Source0:        %{pypi_source}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(setuptools-scm)
BuildRequires:  python3dist(setuptools-scm-git-archive)

%description
One Git library to Rule!

%package -n     python3-%{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
One Git library to Rule!


%prep
%autosetup -n %{srcname}-%{version}
# Remove bundled egg-info
rm -rf %{srcname}.egg-info


%build
%py3_build


%install
%py3_install


%files -n python3-%{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{srcname}
%{python3_sitelib}/%{srcname}-%{version}-py?.?.egg-info


%changelog
* Sat Mar 07 2020 Jiri Popelka <jpopelka@redhat.com> - 0.11.0-1
- New upstream release 0.11.0

* Tue Jan 28 2020 Frantisek Lachman <flachman@redhat.com> - 0.10.0-1
- New upstream release 0.10.0

* Wed Dec 04 2019 Frantisek Lachman <flachman@redhat.com> - 0.9.0-1
- New upstream release 0.9.0

* Mon Sep 30 2019 Frantisek Lachman <flachman@redhat.com> - 0.8.0-1
- New upstream release 0.8.0

* Wed Sep 11 2019 Frantisek Lachman <flachman@redhat.com> - 0.7.0-1
- New upstream release 0.7.0

* Tue Jul 23 2019 Frantisek Lachman <flachman@redhat.com> - 0.6.0-1
- New upstream release 0.6.0

* Fri Jun 28 2019 Frantisek Lachman <flachman@redhat.com> - 0.5.0-1
- New upstream release: 0.5.0

* Tue Jun 11 2019 Jiri Popelka <jpopelka@redhat.com> - 0.4.0-1
- New upstream release: 0.4.0

* Tue May 14 2019 Jiri Popelka <jpopelka@redhat.com> - 0.3.1-1
- patch release: 0.3.1

* Mon May 13 2019 Jiri Popelka <jpopelka@redhat.com> - 0.3.0-1
- New upstream release: 0.3.0

* Wed Mar 27 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.2.0-1
- New upstream release: 0.2.0

* Mon Mar 18 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.1.0-1
- New upstream release: 0.1.0

* Thu Feb 28 2019 Frantisek Lachman <flachman@redhat.com> - 0.0.3-1
- New upstream release 0.0.3

* Tue Feb 26 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.0.2-1
- Initial package.
